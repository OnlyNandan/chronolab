# Self-Improvement Loop & Lessons Learned

*(Review this file at the start of every session. Update it after every correction made by the human.)*

- **2026-09-17**: The Doctor Mode agent hallucinated qualitative words ("improvement"). **Correction**: Ensure strict mathematical prompt constraints (e.g., "increased from X to Y") and actively forbid terms like "improvement" and "worsening".
- **2026-09-17**: `llava:7b` is prone to not being installed on local sandboxes. **Correction**: Always provide a graceful fallback to a text-only model (`qwen2.5:3b`) using PyMuPDF to extract text directly from the PDF if the vision run fails.
