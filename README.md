# AI Writing Assistant

A Python-based Generative AI application powered by Google Gemini API.
Built as a learning and portfolio project.

## Features

- AI-powered content generation
- Automated writing quality review
- AI-assisted draft improvement
- Editable final draft
- Human approval before export
- Word and PDF document export
- Placeholder validation before export
- Application logging
- Activity dashboard
- Automated validation tests
- Error handling

## Technology Stack

- Python
- Google Gemini API
- IPyWidgets
- Python-DOCX
- LibreOffice for PDF conversion
- Google Colab
- Google Drive

## Project Structure

    ai-writing-assistant/
    ├── app.py
    ├── validation.py
    ├── requirements.txt
    ├── README.md
    ├── CASE_STUDY.md
    ├── PORTFOLIO.md
    ├── .gitignore
    ├── logs/
    ├── outputs/
    └── tests/
        └── test_validation.py

## Setup

1. Open Google Colab and mount Google Drive.
2. Install dependencies:

    pip install -r requirements.txt

3. Store your Gemini API key in Google Colab Secrets
   using the name GEMINI_API_KEY.
4. Load the key from Colab Secrets into the
   GEMINI_API_KEY environment variable.
5. Set GEMINI_MODEL to gemini-3.5-flash-lite.
6. Install LibreOffice for PDF export if needed.
7. Run app.py in Google Colab.

## Running Tests

Run:

    python -m unittest discover -s tests -v

## Security

Never upload API keys, passwords, personal documents,
or sensitive logs to GitHub.

Generated documents and application logs are excluded
from Git tracking.

## Project Status

Working Google Colab prototype.
This is not yet a publicly deployed web application.

## Disclaimer

AI-generated content can contain errors.
Users should review and verify content before use.
