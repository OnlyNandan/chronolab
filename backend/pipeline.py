import os
import json
import logging
import pymupdf as fitz  # PyMuPDF (import name kept as `fitz` alias, `fitz` package itself is deprecated)
from PIL import Image
import io
import base64
from pydantic import BaseModel, Field
from typing import List, Optional

try:
    from . import providers, unit_conversion  # imported as backend.pipeline
except ImportError:
    import providers, unit_conversion  # run standalone: python pipeline.py

logger = logging.getLogger("chronolab.pipeline")

# We will use the LLMProvider abstraction (providers.py) to simulate the Strands Agent
# SDK behavior for Phase A and B, since Strands SDK version might vary in how it handles
# images. We'll use pydantic for structured outputs.

class RawLabField(BaseModel):
    test_name: str
    raw_value: float
    raw_unit: str
    date: str
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None

class PhaseAResult(BaseModel):
    fields: List[RawLabField]

class CanonicalLabResult(BaseModel):
    patient_id: str
    test_name_canonical: str
    date: str
    raw_value: float
    raw_unit: str
    standardized_value: float
    standardized_unit: str
    unit_was_converted: bool
    reference_range: dict
    confidence: float
    source_doc_id: str
    source_page: int
    extraction_fallback_used: bool = False

class PhaseBResult(BaseModel):
    canonical_fields: List[CanonicalLabResult]

def get_image_base64(pixmap):
    img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def extract_text_fallback(page):
    return page.get_text("text")

PHASE_A_PROMPT = """
Extract the following lab result fields from this page:
- test_name
- raw_value
- raw_unit
- date (YYYY-MM-DD format)
- reference_range_low (if present)
- reference_range_high (if present)
Output ONLY valid JSON matching this schema:
{ "fields": [ { "test_name": "...", "raw_value": 0.0, "raw_unit": "...", "date": "...", "reference_range_low": 0.0, "reference_range_high": 0.0 } ] }
"""

def phase_a_vision_extraction(pdf_path: str, provider: providers.LLMProvider) -> list:
    """Phase A: Vision model to extract raw fields."""
    print(f"[Phase A] Processing {pdf_path} with Vision model...")
    results = []

    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()
        img_b64 = get_image_base64(pix)

        fallback_used = False
        try:
            data = provider.extract_from_image(img_b64, PHASE_A_PROMPT)
        except Exception as e:
            fallback_used = True
            logger.warning(
                f"[Phase A] Vision extraction failed on {pdf_path} page {page_num + 1} "
                f"(fallback to text extraction). Error: {e}"
            )
            text = extract_text_fallback(page)
            fallback_prompt = PHASE_A_PROMPT + f"\n\nHere is the extracted text from the page:\n{text}"
            try:
                data = provider.extract_from_text(fallback_prompt)
            except Exception as fallback_error:
                logger.warning(f"[Phase A] Text fallback also failed to parse JSON: {fallback_error}")
                continue

        if "fields" in data:
            for item in data["fields"]:
                item["page"] = page_num + 1
                item["extraction_fallback_used"] = fallback_used
            results.extend(data["fields"])

    return results

PHASE_B_SYSTEM_PROMPT = """
You are a medical data standardization agent. Your job is ONLY to organize data, never interpret it.
No diagnoses, no treatment-efficacy judgments, no "this is good/bad".

Given raw lab fields, canonicalize the test_name to one of: "HbA1c", "Fasting Glucose", "Total Cholesterol", "LDL Cholesterol".

Do NOT perform unit conversion or any arithmetic — pass raw_value and raw_unit through unchanged.
Unit standardization is computed deterministically outside this step.

Assign a confidence score (0.0 to 1.0). If you are unsure about a mapping or the raw data looks corrupt, lower the confidence below 0.7.

Output ONLY valid JSON matching this schema:
{
  "canonical_fields": [
    {
      "patient_id": "...",
      "test_name_canonical": "...",
      "date": "...",
      "raw_value": 0.0,
      "raw_unit": "...",
      "reference_range": {"low": 0.0, "high": 0.0},
      "confidence": 0.9,
      "source_doc_id": "...",
      "source_page": 1
    }
  ]
}
"""

def phase_b_reasoning(raw_fields: list, patient_id: str, source_doc_id: str, provider: providers.LLMProvider) -> list:
    """Phase B: Reasoning model canonicalizes test names; unit conversion is deterministic Python."""
    print(f"[Phase B] Canonicalizing {len(raw_fields)} fields...")

    prompt = f"Raw fields: {json.dumps(raw_fields)}\nPatient ID: {patient_id}\nSource Doc ID: {source_doc_id}"
    full_prompt = PHASE_B_SYSTEM_PROMPT + "\n\n" + prompt

    try:
        data = provider.extract_from_text(full_prompt)
        canonical_fields = data.get("canonical_fields", [])
    except Exception as e:
        print(f"Phase B reasoning failed: {e}")
        return []

    # Fallback flags don't survive the model round-trip, so re-attach them from raw_fields
    # (matched by source_page) before computing standardized values.
    fallback_by_page = {
        f.get("page"): f.get("extraction_fallback_used", False) for f in raw_fields
    }

    for field in canonical_fields:
        standardized_value, standardized_unit, unit_was_converted = unit_conversion.standardize(
            field.get("test_name_canonical", ""),
            field.get("raw_value", 0.0),
            field.get("raw_unit", ""),
        )
        field["standardized_value"] = standardized_value
        field["standardized_unit"] = standardized_unit
        field["unit_was_converted"] = unit_was_converted
        field["extraction_fallback_used"] = fallback_by_page.get(field.get("source_page"), False)

    return canonical_fields

def run_pipeline(pdf_path: str):
    filename = os.path.basename(pdf_path)
    # Extract patient_id from mock filename (e.g., report_1_PT-1001_2025-12-20.pdf)
    parts = filename.split('_')
    patient_id = parts[2] if len(parts) >= 3 else "UNKNOWN"

    provider = providers.get_provider()

    raw_fields = phase_a_vision_extraction(pdf_path, provider)
    if not raw_fields:
        print(f"No fields extracted for {filename}.")
        return []

    canonical_fields = phase_b_reasoning(raw_fields, patient_id, filename, provider)
    return canonical_fields

if __name__ == "__main__":
    import glob
    # Test pipeline on one fixture
    fixtures = glob.glob(os.path.join(os.path.dirname(__file__), "../data/*.pdf"))
    if fixtures:
        print(f"Testing pipeline on {fixtures[0]}")
        result = run_pipeline(fixtures[0])
        print("Final Output:")
        print(json.dumps(result, indent=2))
    else:
        print("No fixtures found in data/")
