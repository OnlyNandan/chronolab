import os
import json
import pymupdf as fitz  # PyMuPDF (import name kept as `fitz` alias, `fitz` package itself is deprecated)
from PIL import Image
import io
import base64
from pydantic import BaseModel, Field
from typing import List, Optional
import ollama

# We will use ollama directly to simulate the Strands Agent SDK behavior for Phase A and B,
# since Strands SDK version might vary in how it handles images in ollama.
# We'll use pydantic for structured outputs.

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

class PhaseBResult(BaseModel):
    canonical_fields: List[CanonicalLabResult]

def get_image_base64(pixmap):
    img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def extract_text_fallback(page):
    return page.get_text("text")

def phase_a_vision_extraction(pdf_path: str) -> list:
    """Phase A: Vision model to extract raw fields."""
    print(f"[Phase A] Processing {pdf_path} with Vision model...")
    results = []
    
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()
        img_b64 = get_image_base64(pix)
        
        prompt = """
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
        
        try:
            # Try to use vision model llava:7b
            response = ollama.chat(
                model='llava:7b',
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [img_b64]
                }],
                format='json',
                options={'temperature': 0.1}
            )
            data = json.loads(response['message']['content'])
            
            # Basic validation
            if "fields" in data:
                for item in data["fields"]:
                    item["page"] = page_num + 1
                results.extend(data["fields"])
                
        except Exception as e:
            print(f"Vision model failed (maybe llava:7b not pulled?). Fallback to text extraction. Error: {e}")
            text = extract_text_fallback(page)
            # Fallback to qwen2.5:3b with text
            fallback_prompt = prompt + f"\n\nHere is the extracted text from the page:\n{text}"
            response = ollama.chat(
                model='qwen2.5:3b',
                messages=[{
                    'role': 'user',
                    'content': fallback_prompt
                }],
                format='json',
                options={'temperature': 0.1}
            )
            try:
                data = json.loads(response['message']['content'])
                if "fields" in data:
                    for item in data["fields"]:
                        item["page"] = page_num + 1
                    results.extend(data["fields"])
            except:
                print("Text fallback failed to parse JSON.")
                pass

    return results

def phase_b_reasoning(raw_fields: list, patient_id: str, source_doc_id: str) -> list:
    """Phase B: Reasoning model to canonicalize and convert units."""
    print(f"[Phase B] Canonicalizing {len(raw_fields)} fields...")
    
    system_prompt = """
    You are a medical data standardization agent. Your job is ONLY to organize data, never interpret it.
    No diagnoses, no treatment-efficacy judgments, no "this is good/bad".
    
    Given raw lab fields, canonicalize the test_name to one of: "HbA1c", "Fasting Glucose", "Total Cholesterol", "LDL Cholesterol".
    Standardize units:
    - HbA1c to % (if mmol/mol, convert to %. Formula: % = (mmol/mol / 10.929) + 2.15)
    - Glucose to mg/dL (if mmol/L, convert to mg/dL. Formula: mg/dL = mmol/L * 18.0182)
    - Cholesterol to mg/dL (if mmol/L, convert to mg/dL. Formula: mg/dL = mmol/L * 38.67)
    
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
          "standardized_value": 0.0,
          "standardized_unit": "...",
          "unit_was_converted": false,
          "reference_range": {"low": 0.0, "high": 0.0},
          "confidence": 0.9,
          "source_doc_id": "...",
          "source_page": 1
        }
      ]
    }
    """
    
    prompt = f"Raw fields: {json.dumps(raw_fields)}\nPatient ID: {patient_id}\nSource Doc ID: {source_doc_id}"
    
    try:
        response = ollama.chat(
            model='qwen2.5:3b',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            format='json',
            options={'temperature': 0.1}
        )
        data = json.loads(response['message']['content'])
        return data.get("canonical_fields", [])
    except Exception as e:
        print(f"Phase B reasoning failed: {e}")
        return []

def run_pipeline(pdf_path: str):
    filename = os.path.basename(pdf_path)
    # Extract patient_id from mock filename (e.g., report_1_PT-1001_2025-12-20.pdf)
    parts = filename.split('_')
    patient_id = parts[2] if len(parts) >= 3 else "UNKNOWN"
    
    raw_fields = phase_a_vision_extraction(pdf_path)
    if not raw_fields:
        print(f"No fields extracted for {filename}.")
        return []
        
    canonical_fields = phase_b_reasoning(raw_fields, patient_id, filename)
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
