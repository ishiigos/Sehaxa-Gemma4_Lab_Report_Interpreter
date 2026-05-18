import os
import re
import markdown
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request

try:
    from google import genai
except Exception:
    genai = None

try:
    from PIL import Image
    import pytesseract
except Exception:
    Image = None
    pytesseract = None

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8MB

REFERENCE_RANGES = {
    "hemoglobin": {"label": "Hemoglobin", "unit": "g/dL", "low": 12.0, "high": 15.5, "note": "Adult female reference range; varies by lab, age, pregnancy status, and altitude."},
    "wbc": {"label": "White Blood Cell Count", "unit": "cells/µL", "low": 4000, "high": 11000, "note": "May vary slightly by laboratory."},
    "platelets": {"label": "Platelet Count", "unit": "cells/µL", "low": 150000, "high": 450000, "note": "Used to assess clotting and marrow/inflammatory patterns."},
    "fasting_glucose": {"label": "Fasting Blood Glucose", "unit": "mg/dL", "low": 70, "high": 99, "note": "Fasting status matters. Diabetes diagnosis requires clinical confirmation."},
    "hba1c": {"label": "HbA1c", "unit": "%", "low": 4.0, "high": 5.6, "note": "Reflects ~3 month average blood glucose; interpretation depends on clinical context."},
    "tsh": {"label": "TSH", "unit": "mIU/L", "low": 0.4, "high": 4.0, "note": "Thyroid ranges vary by pregnancy, age, and assay."},
    "vitamin_d": {"label": "Vitamin D", "unit": "ng/mL", "low": 20, "high": 50, "note": "Cutoffs vary; many Indian patients have insufficiency/deficiency."},
    "b12": {"label": "Vitamin B12", "unit": "pg/mL", "low": 200, "high": 900, "note": "Borderline values may need MMA/homocysteine depending on symptoms."},
    "alt": {"label": "ALT / SGPT", "unit": "U/L", "low": 7, "high": 56, "note": "Liver enzyme; interpret with AST, bilirubin, alcohol, medicines, fatty liver risk."},
    "creatinine": {"label": "Creatinine", "unit": "mg/dL", "low": 0.6, "high": 1.1, "note": "Kidney marker; depends on muscle mass, hydration, age, sex."},
}

# Regex patterns are intentionally simple for the demo.
# They are designed to work with common report text, not every possible lab format.
OCR_PATTERNS = {
    "hemoglobin": [
        r"(?:hemoglobin|haemoglobin|hb)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)",
    ],
    "wbc": [
        r"(?:wbc|white blood cell(?: count)?|total leukocyte count|tlc)\s*[:\-]?\s*(\d{3,6}(?:\.\d+)?)",
    ],
    "platelets": [
        r"(?:platelet(?: count)?|platelets)\s*[:\-]?\s*(\d{4,7}(?:\.\d+)?)",
    ],
    "fasting_glucose": [
        r"(?:fasting glucose|fasting blood sugar|fbs|glucose fasting)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)",
    ],
    "hba1c": [
        r"(?:hba1c|glycated hemoglobin)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)",
    ],
    "tsh": [
        r"(?:tsh|thyroid stimulating hormone)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)",
    ],
    "vitamin_d": [
        r"(?:vitamin d|25-oh vitamin d|25 hydroxy vitamin d)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)",
    ],
    "b12": [
        r"(?:vitamin b12|b12|cobalamin)\s*[:\-]?\s*(\d{2,4}(?:\.\d+)?)",
    ],
    "alt": [
        r"(?:alt|sgpt|alanine aminotransferase)\s*[:\-]?\s*(\d{1,4}(?:\.\d+)?)",
    ],
    "creatinine": [
        r"(?:creatinine|serum creatinine)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)",
    ],
}

def clean_ocr_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "webp"}

def extract_text_from_image(file_storage):
    if Image is None or pytesseract is None:
        return "", "OCR dependencies are missing. Install pytesseract and pillow, plus the Tesseract system app."

    image = Image.open(file_storage.stream).convert("RGB")
    text = pytesseract.image_to_string(image)
    return text, None

def extract_values_from_ocr(text):
    cleaned = clean_ocr_text(text).lower()
    extracted = {}

    for key, patterns in OCR_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, cleaned, flags=re.IGNORECASE)
            if match:
                extracted[key] = match.group(1)
                break

    return extracted

def classify_value(key, raw_value):
    try:
        value = float(raw_value)
    except Exception:
        return {"status": "unknown", "flag": "Could not parse", "value": raw_value}

    ref = REFERENCE_RANGES.get(key)
    if not ref:
        return {"status": "unknown", "flag": "No local range available", "value": value}

    if value < ref["low"]:
        status = "low"
    elif value > ref["high"]:
        status = "high"
    else:
        status = "normal"

    return {"status": status, "flag": status.upper(), "value": value}

def build_structured_report(values):
    report = []
    for key, meta in REFERENCE_RANGES.items():
        raw = str(values.get(key, "")).strip()
        if raw:
            result = classify_value(key, raw)
            report.append({
                "key": key,
                "name": meta["label"],
                "value": result["value"],
                "unit": meta["unit"],
                "status": result["status"],
                "reference_range": f"{meta['low']}–{meta['high']} {meta['unit']}",
                "note": meta["note"]
            })
    return report

def gemma_prompt(report, language_mode):
    return f"""
You are Sehaxa, a careful health-literacy assistant for Indian users.

Task:
Explain the following lab report values in simple patient-friendly language.
Do NOT diagnose.
Do NOT prescribe medicines.
Do NOT create panic.
Recommend consulting a qualified clinician for abnormal values.

For each parameter:
1. What this test usually indicates
2. Whether the value is low/normal/high based on supplied reference range
3. Common non-diagnostic reasons it may be abnormal
4. What the user should discuss with a doctor
5. Hindi explanation if language_mode is bilingual or hindi

Language mode: {language_mode}

Return in this structure:
- Overall Summary
- Parameter-wise Insights
- Questions to Ask Your Doctor
- Safety Note

Structured report:
{json.dumps(report, indent=2)}
"""

def fallback_response(report, language_mode):
    lines = []
    abnormal = [r for r in report if r["status"] in ["low", "high"]]
    if abnormal:
        lines.append(f"Overall Summary: Sehaxa found {len(abnormal)} value(s) outside the sample reference ranges. This is not a diagnosis, but these values are worth discussing with a doctor.")
    else:
        lines.append("Overall Summary: The entered values appear within the sample reference ranges used by this demo. Always compare with your lab's printed ranges and your doctor's advice.")

    lines.append("\nParameter-wise Insights:")
    for r in report:
        lines.append(f"\n• {r['name']}: {r['value']} {r['unit']} ({r['status'].upper()})")
        lines.append(f"  Reference used: {r['reference_range']}")
        if r["status"] == "low":
            lines.append("  Meaning: This value is below the demo reference range.")
            lines.append("  Possible reasons: nutritional deficiency, recent illness, chronic disease, medication effects, or normal variation depending on context.")
        elif r["status"] == "high":
            lines.append("  Meaning: This value is above the demo reference range.")
            lines.append("  Possible reasons: inflammation, infection, metabolic stress, diet/lifestyle factors, medication effects, or lab/context variation.")
        else:
            lines.append("  Meaning: This value is within the demo reference range.")
        lines.append(f"  Context note: {r['note']}")

    lines.append("\nQuestions to Ask Your Doctor:")
    lines.append("• Is this result significant for my age, sex, symptoms, and medical history?")
    lines.append("• Should I repeat the test or do a follow-up test?")
    lines.append("• Are medicines, diet, infection, hydration, or lifestyle affecting this value?")

    lines.append("\nSafety Note: Sehaxa is an educational tool and not a substitute for medical advice, diagnosis, or treatment.")

    if language_mode in ["hindi", "bilingual"]:
        lines.append("\nहिंदी सारांश:")
        lines.append("यह रिपोर्ट केवल समझाने के लिए है। यह निदान या इलाज की सलाह नहीं देती। जिन मानों में बदलाव दिख रहा है, उन्हें डॉक्टर के साथ ज़रूर चर्चा करें।")

    return "\n".join(lines)

def call_gemma(report, language_mode):
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

    if not api_key or genai is None:
        return fallback_response(report, language_mode), "fallback"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=gemma_prompt(report, language_mode),
        )
        return response.text, model_name
    except Exception as e:
        return fallback_response(report, language_mode) + f"\n\n[Gemma API fallback used because: {str(e)}]", "fallback"

def render_markdown(text):
    return markdown.markdown(
        text,
        extensions=["extra", "nl2br"]
    )

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    report = None
    provider = None
    language_mode = "bilingual"
    form_values = {}
    ocr_text = None
    ocr_error = None
    extracted_values = {}

    if request.method == "POST":
        language_mode = request.form.get("language_mode", "bilingual")
        action = request.form.get("action", "decode_manual")

        if action == "extract_ocr":
            image_file = request.files.get("report_image")
            if not image_file or image_file.filename == "":
                ocr_error = "Please upload a report image first."
            elif not allowed_file(image_file.filename):
                ocr_error = "Please upload a PNG, JPG, JPEG, or WEBP image."
            else:
                filename = secure_filename(image_file.filename)
                # OCR directly from memory; no need to persist patient data.
                ocr_text, ocr_error = extract_text_from_image(image_file)
                if ocr_text:
                    extracted_values = extract_values_from_ocr(ocr_text)
                    form_values.update(extracted_values)

        elif action == "decode_ocr":
            ocr_text = request.form.get("ocr_text", "")
            extracted_values = extract_values_from_ocr(ocr_text)
            form_values.update(extracted_values)
            report = build_structured_report(form_values)
            if report:
                result, provider = call_gemma(report, language_mode)
                result = render_markdown(result)
            else:
                result = "Sehaxa could not detect supported lab values from the OCR text. Please enter values manually or use a clearer image."
                provider = "none"

        else:
            for key in REFERENCE_RANGES.keys():
                form_values[key] = request.form.get(key, "").strip()
            report = build_structured_report(form_values)
            if report:
                result, provider = call_gemma(report, language_mode)
                result = render_markdown(result)
            else:
                result = "Please enter at least one lab value or upload a report image."
                provider = "none"

    return render_template(
        "index.html",
        result=result,
        report=report,
        provider=provider,
        reference_ranges=REFERENCE_RANGES,
        language_mode=language_mode,
        form_values=form_values,
        ocr_text=ocr_text,
        ocr_error=ocr_error,
        extracted_values=extracted_values,
        year=datetime.now().year,
    )

if __name__ == "__main__":
    app.run(debug=True)
