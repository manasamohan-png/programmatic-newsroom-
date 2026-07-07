import os
import sys
import argparse
import requests
import urllib.parse
from dotenv import load_dotenv, set_key

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
load_dotenv(dotenv_path)

CLIENT_ID = os.getenv('ZOOM_CLIENT_ID')
REFRESH_TOKEN = os.getenv('ZOOM_REFRESH_TOKEN')

if not CLIENT_ID or not REFRESH_TOKEN:
    print("Error: ZOOM_CLIENT_ID or ZOOM_REFRESH_TOKEN not found in .env.", file=sys.stderr)
    sys.exit(1)

def refresh_access_token():
    token_url = "https://zoom.us/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        access_token = token_data.get('access_token')
        new_refresh_token = token_data.get('refresh_token')
        
        if new_refresh_token:
            set_key(dotenv_path, 'ZOOM_REFRESH_TOKEN', new_refresh_token)
            
        return access_token
    except Exception as e:
        print(f"Error refreshing access token: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Fetch Zoom AI Companion meeting summary for a specific instance.")
    parser.add_argument('--meeting-uuid', required=True, help="The meeting UUID or ID of the instance.")
    args = parser.parse_args()
    
    access_token = refresh_access_token()
    
    # Double-encode the UUID as required by Zoom API for meeting summaries
    encoded_uuid = urllib.parse.quote(urllib.parse.quote(args.meeting_uuid, safe=''), safe='')
    
    url = f"https://api.zoom.us/v2/meetings/{encoded_uuid}/meeting_summary"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            print(f"No summary found for meeting instance '{args.meeting_uuid}'. Ensure it is a past instance and AI Companion summary was enabled.", file=sys.stderr)
            sys.exit(0)
            
        response.raise_for_status()
        data = response.json()
        
        summary_title = data.get('meeting_host_email', 'Meeting') + "'s Summary"
        print(f"# Zoom Meeting Summary\n")
        print(f"- **Meeting Topic**: {data.get('meeting_topic', 'N/A')}")
        print(f"- **Host Email**: {data.get('meeting_host_email', 'N/A')}")
        print(f"- **Start Time**: {data.get('meeting_start_time', 'N/A')}\n")
        
        details = data.get('summary_details', [])
        if not details:
            print("No highlights or next steps generated for this summary.")
        else:
            for detail in details:
                label = detail.get('label', 'Summary')
                value = detail.get('value', '').replace('\n', '\n  ')
                print(f"### {label}\n{value}\n")
                
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
