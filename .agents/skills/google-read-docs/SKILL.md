---
name: google-read-docs
description: Reads a google docs file and downloads it.
---

# google-read-docs

This skill connects to Google Docs/Drive using the Google OAuth credentials loaded via `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` environment variables.

It can extract plain text directly to the console or download/export a Google Doc in various formats.

## Usage

Run the Python script, providing the Google Doc URL or ID.

### Command to Execute
```bash
# Read and print plain text of Google Doc
python3 .agents/skills/google-read-docs/scripts/read_doc.py "https://docs.google.com/document/d/1X-x-xxxxx/edit"

# Download Google Doc as a PDF
python3 .agents/skills/google-read-docs/scripts/read_doc.py "1X-x-xxxxx" --output path/to/document.pdf

# Download Google Doc as a Word Document
python3 .agents/skills/google-read-docs/scripts/read_doc.py "1X-x-xxxxx" --output path/to/document.docx
```

## Options
- `doc_url_or_id`: Positional argument. The Google Doc URL or Document ID.
- `--output`, `-o`: (Optional) Local path where the exported document will be saved.
- `--format`, `-f`: (Optional) Explicit format to export. Supported values: `txt`, `pdf`, `docx`, `html`, `rtf`, `odt`. If not specified and `--output` is provided, it is auto-inferred from the file extension.

## Prerequisites
- Active `.env` file must contain valid `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` variables.
- Python dependencies `google-api-python-client`, `google-auth-httplib2`, and `google-auth-oauthlib` must be installed.
