# Sehaxa — AI Lab Report Interpreter for India

Sehaxa is a Gemma 4 powered health-literacy prototype that helps Indian users understand common lab report values in simple English and Hindi.

## New in this version

This version includes:
- report image upload
- OCR text extraction using Tesseract
- regex-based extraction of common lab values
- manual correction fallback
- Gemma 4 explanation layer
- bilingual English/Hindi output option

## Problem

Many patients receive lab reports filled with technical terms, numbers, and unexplained reference ranges. In India, this is amplified by language barriers, limited doctor-patient time, and varying levels of health literacy.

## Solution

Sehaxa turns a report image or manually entered lab values into:
- simple explanations
- low/normal/high interpretation
- common non-diagnostic reasons for abnormal values
- questions to ask a doctor
- Hindi-friendly summaries

## Tech Stack

- Python
- Flask
- Tesseract OCR
- pytesseract
- Pillow
- Google GenAI SDK
- Gemma 4 via Gemini API
- HTML/CSS frontend

## Gemma 4 Usage

This prototype calls Gemma 4 through the Gemini API using:

```python
model="gemma-4-26b-a4b-it"
```

The app sends structured lab values and reference ranges to Gemma 4, then requests safe, patient-friendly explanations. It uses a constrained prompt to reduce medical overclaiming and includes a fallback deterministic explanation mode for demo resilience.

## Run Locally

### 1. Install Tesseract

Mac:

```bash
brew install tesseract
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

Windows:
Install Tesseract from the official installer and add it to PATH.

### 2. Install Python dependencies

```bash
cd sehaxa_mvp_ocr
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add API key

```bash
export GOOGLE_API_KEY="your_api_key_here"
export GEMMA_MODEL="gemma-4-26b-a4b-it"
```

### 4. Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Demo Without API Key

The app includes fallback mode, so it still works without an API key. For judging, use a real Gemma 4 API key and mention the model used in the video/writeup.

## Suggested Demo Case

Use a clear report screenshot or manually enter:
- Hemoglobin: 9.5
- WBC: 12500
- TSH: 2.5
- Vitamin D: 12
- Vitamin B12: 100

## OCR Limitations

This is a hackathon MVP. OCR may fail on blurry images, complex report layouts, handwriting, or unusual lab names. The app intentionally keeps manual correction because safety matters in health-related applications.

## Safety

Sehaxa is not a diagnostic system. It does not prescribe treatment or replace a qualified clinician. It is an educational assistant for health literacy.

## Hackathon Tracks

Best fit:
- Health & Sciences
- Main Track
