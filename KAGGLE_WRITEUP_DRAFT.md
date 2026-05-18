# Sehaxa: AI-Powered Lab Report Interpreter for Accessible Healthcare in India

## Subtitle
Sehaxa uses Gemma 4 to transform lab report photos and values into simple, bilingual, safety-aware health explanations for Indian users.

## Problem
Millions of people receive diagnostic lab reports without understanding what the numbers mean. A report may say “HbA1c”, “TSH”, “ALT”, “Vitamin D”, or “Hemoglobin”, but the patient is often left to search online, panic, or wait for a rushed explanation. In India, this problem is intensified by language barriers, low health literacy, uneven access to doctors, and the growing use of digital lab reports.

Sehaxa addresses this gap by helping people understand their own health information in a responsible, non-diagnostic way.

## Solution
Sehaxa is an AI lab report interpreter that lets users upload a lab report image or enter lab values manually. It extracts common values using OCR, structures them, compares them with sample reference ranges, and uses Gemma 4 to generate patient-friendly explanations in English and Hindi.

The output explains:
- what the test usually indicates
- whether the value appears low, normal, or high
- common non-diagnostic reasons why it may be abnormal
- questions the user should ask a qualified doctor
- a Hindi-friendly summary for accessibility

## Why Gemma 4
Gemma 4 is suitable for Sehaxa because the project needs multilingual generation, reasoning over structured values, safety-aware responses, and the possibility of local-first or privacy-preserving deployment. In this prototype, Gemma 4 is used to convert structured lab report data into understandable explanations while following a constrained system prompt that prevents diagnosis, treatment instructions, or panic-driven language.

The implementation uses the hosted Gemini API path for Gemma 4 prototyping with `gemma-4-26b-a4b-it`. This keeps the prototype lightweight and reproducible while still making Gemma 4 central to the reasoning and explanation layer.

## Architecture
The system follows a practical MVP architecture:

Report Image / Manual Input → Flask Web App → Tesseract OCR → Regex Lab Value Extraction → Reference Range Layer → Gemma 4 Prompt → Bilingual Explanation → Safety Note

The app contains a reference-range layer for common tests and passes structured JSON to Gemma 4. Gemma 4 then generates the explanation in a controlled format:
1. Overall Summary
2. Parameter-wise Insights
3. Questions to Ask Your Doctor
4. Safety Note

This architecture keeps the model grounded in supplied values and reduces the risk of vague or unsupported output.

## Technical Execution
The prototype is built with Python and Flask. The frontend is a clean, responsive HTML/CSS interface where users can upload a lab report image or enter common lab values. The backend extracts text using Tesseract OCR, detects supported lab parameters with regular expressions, flags low/normal/high values using local reference ranges, and sends the structured report to Gemma 4.

The system includes fallback deterministic output so that the demo remains functional even if the API is unavailable. Manual correction is intentionally preserved because OCR is imperfect, and safety matters in health-related use cases.

## Safety and Trust
Because lab reports are medically sensitive, Sehaxa is designed as a health-literacy assistant rather than a diagnostic tool. It does not prescribe medicine, diagnose disease, or replace clinical care. Every output includes a safety note and directs users to discuss abnormal results with a qualified clinician.

The constrained prompt asks Gemma 4 to explain uncertainty, avoid diagnosis, and suggest doctor-facing questions instead of medical conclusions.

## Impact
Sehaxa fits the Health & Sciences and Digital Equity & Inclusivity tracks. It helps bridge the gap between complex medical data and everyday understanding, especially for Indian users who may prefer Hindi explanations. The larger vision is to support more Indian languages, PDF report parsing, lab-specific reference range extraction, local-first inference, and clinically reviewed health-literacy templates.

## Future Work
Future improvements include:
- PDF report parsing
- support for regional Indian languages
- lab-specific reference range extraction
- retrieval-augmented medical knowledge grounding
- on-device Gemma deployment for privacy-sensitive environments
- clinician-reviewed explanation templates
