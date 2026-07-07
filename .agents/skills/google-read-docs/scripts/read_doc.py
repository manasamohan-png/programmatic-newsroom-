#!/usr/bin/env python3
import os
import sys
import re
import argparse
import io

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    print("Error: Missing required Python packages.", file=sys.stderr)
    print("Run: pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib", file=sys.stderr)
    sys.exit(1)

# Format to Google Drive Export MIME Types
FORMAT_MIME_TYPES = {
    'txt': 'text/plain',
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'html': 'text/html',
    'rtf': 'application/rtf',
    'odt': 'application/vnd.oasis.opendocument.text'
}

EXTENSION_TO_FORMAT = {
    '.txt': 'txt',
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.html': 'html',
    '.htm': 'html',
    '.rtf': 'rtf',
    '.odt': 'odt'
}

def load_env():
    """Load env variables from .env file checking current directory and parents."""
    cwd = os.getcwd()
    search_dirs = [cwd]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        search_dirs.append(current_dir)
        current_dir = os.path.dirname(current_dir)
        
    for d in search_dirs:
        env_path = os.path.join(d, '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip()
                            if val.startswith('"') and val.endswith('"'): val = val[1:-1]
                            elif val.startswith("'") and val.endswith("'"): val = val[1:-1]
                            os.environ[key] = val
            break

def extract_document_id(input_str):
    """Extract ID from a full Google Docs URL or return it directly if it's already an ID."""
    match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', input_str)
    if match:
        return match.group(1)
    return input_str

def main():
    load_env()
    
    parser = argparse.ArgumentParser(description="Read a Google Docs file and download/print it.")
    parser.add_argument('doc_url_or_id', type=str, help="Google Doc URL or Document ID.")
    parser.add_argument('--output', '-o', type=str, default=None, help="Local file path to save the downloaded file.")
    parser.add_argument('--format', '-f', type=str, default=None, choices=list(FORMAT_MIME_TYPES.keys()),
                        help="Export format (default: auto-detected or txt).")
    
    args = parser.parse_args()
    
    doc_id = extract_document_id(args.doc_url_or_id)
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        print("Error: Required Google authentication environment variables are missing.", file=sys.stderr)
        print("Ensure GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN are set in .env.", file=sys.stderr)
        sys.exit(1)
        
    # Determine the target format
    target_format = args.format
    if not target_format:
        if args.output:
            _, ext = os.path.splitext(args.output.lower())
            target_format = EXTENSION_TO_FORMAT.get(ext, 'txt')
        else:
            target_format = 'txt'
            
    # Binary safety check
    if not args.output and target_format in ['pdf', 'docx', 'odt']:
        print(f"Error: Format '{target_format}' is binary and cannot be printed to stdout.", file=sys.stderr)
        print("Please specify an output file path using --output or -o.", file=sys.stderr)
        sys.exit(1)
        
    mime_type = FORMAT_MIME_TYPES[target_format]
    
    # Drive scope to read and export Google Docs
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    print("Authenticating using Google OAuth Refresh Token...", file=sys.stderr)
    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=creds)
        
        # Get document title
        print(f"Fetching metadata for Document ID: {doc_id}...", file=sys.stderr)
        file_metadata = service.files().get(fileId=doc_id, fields='name', supportsAllDrives=True).execute()
        doc_title = file_metadata.get('name', 'Untitled Document')
        print(f"Found document: \"{doc_title}\"", file=sys.stderr)
        
        print(f"Exporting document as format: {target_format} ({mime_type})...", file=sys.stderr)
        
        request = service.files().export_media(fileId=doc_id, mimeType=mime_type)
        exported_bytes = io.BytesIO()
        downloader = MediaIoBaseDownload(exported_bytes, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%", file=sys.stderr)
                
        exported_bytes.seek(0)
        content = exported_bytes.read()
        
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            with open(args.output, 'wb') as f:
                f.write(content)
            print(f"Successfully saved to: {args.output}", file=sys.stderr)
        else:
            # Print text content to stdout
            try:
                text_content = content.decode('utf-8')
                sys.stdout.write(text_content)
                if not text_content.endswith('\n'):
                    sys.stdout.write('\n')
            except UnicodeDecodeError:
                sys.stdout.buffer.write(content)
                
    except Exception as e:
        print(f"Google API Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
Step 1: Find the last creator 
Look through this document: https://docs.google.com/document/d/1LOPh1RA07FL_QgjvLN8jmpheppu6TtdxDUGvlsP5KXY/edit?tab=t.0 and find the last creator suggested 

