# AI Writing Assistant

A Python-based Generative AI application powered by
the Google Gemini API.

## Features

- AI-powered content generation
- Automated writing quality review
- Draft improvement
- Human approval workflow
- Word document export
- Application logging
- User-friendly error handling

## Technology Stack

- Python
- Google Gemini API
- IPyWidgets
- Python-DOCX
- Google Colab
- Google Drive

## Project Structure

ai-writing-assistant/
    app.py
    README.md
    PORTFOLIO.md
    CASE_STUDY.md
    .gitignore
    logs/
    outputs/

## Setup

1. Open the project in Google Colab.
2. Install the required packages:

   pip install google-genai python-docx ipywidgets

3. Store your Gemini API key securely in
   Google Colab Secrets using the name GEMINI_API_KEY.

4. Load the API key from Colab Secrets into
   the GEMINI_API_KEY environment variable.

5. Set GEMINI_MODEL to gemini-3.5-flash-lite.

6. Run app.py in Google Colab.

## Security

Never upload API keys, passwords, personal documents,
or sensitive logs to GitHub.

The .gitignore file excludes selected generated files
and sensitive file patterns.

## Project Status

Working Google Colab prototype.

This is not yet a publicly deployed web application.

## Disclaimer

AI-generated content can contain errors.
Users should review and verify content before use.
