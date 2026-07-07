import os
import sys
import argparse
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone
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

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"Error: Invalid date format for '{date_str}'. Expected YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

def fetch_meetings(access_token, start_date, end_date):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    url = "https://api.zoom.us/v2/users/me/meetings"
    params = {
        "type": "scheduled",
        "page_size": 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch meetings: {e}", file=sys.stderr)
        sys.exit(1)
        
    meetings = data.get('meetings', [])
    occurrences = []
    
    for mtg in meetings:
        mtg_id = mtg.get('id')
        topic = mtg.get('topic')
        agenda = mtg.get('agenda', 'N/A')
        if len(agenda) > 60:
            agenda = agenda[:57] + "..."
            
        # 1. Past instances
        instances_url = f"https://api.zoom.us/v2/past_meetings/{mtg_id}/instances"
        try:
            instances_resp = requests.get(instances_url, headers=headers)
            if instances_resp.status_code == 200:
                instances_data = instances_resp.json()
                for inst in instances_data.get('meetings', []):
                    inst_uuid = inst.get('uuid')
                    start_time_str = inst.get('start_time')
                    if start_time_str:
                        # Zoom returns ISO 8601 strings like "2025-10-28T15:29:46Z"
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_date <= start_time <= end_date:
                            occurrences.append({
                                'topic': topic,
                                'meeting_id': mtg_id,
                                'uuid': inst_uuid,
                                'date': start_time,
                                'type': 'Past',
                                'agenda': agenda
                            })
        except requests.exceptions.RequestException:
            pass # ignore failures listing instances for specific templates
            
        # 2. Scheduled upcoming instances
        start_time_str = mtg.get('start_time')
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            if start_date <= start_time <= end_date:
                occurrences.append({
                    'topic': topic,
                    'meeting_id': mtg_id,
                    'uuid': mtg.get('uuid', 'N/A'),
                    'date': start_time,
                    'type': 'Upcoming',
                    'agenda': agenda
                })
                
    # Sort occurrences by date descending (newest first)
    occurrences.sort(key=lambda x: x['date'], reverse=True)
    return occurrences

def main():
    parser = argparse.ArgumentParser(description="List Zoom meetings (scheduled and past) for a specific date range.")
    parser.add_argument('--start-date', help="Start date in YYYY-MM-DD format. Defaults to 30 days ago.")
    parser.add_argument('--end-date', help="End date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument('--search', help="Search term to filter meetings by topic or agenda.")
    args = parser.parse_args()
    
    # Parse date range
    if args.end_date:
        end_dt = parse_date(args.end_date)
    else:
        end_dt = datetime.now(timezone.utc)
        
    # Make end_dt inclusive of the full day
    end_dt = end_dt.replace(hour=23, minute=59, second=59)
    
    if args.start_date:
        start_dt = parse_date(args.start_date)
    else:
        start_dt = end_dt - timedelta(days=30)
        
    start_dt = start_dt.replace(hour=0, minute=0, second=0)
    
    access_token = refresh_access_token()
    meetings = fetch_meetings(access_token, start_dt, end_dt)
    
    if args.search:
        search_query = args.search.lower()
        meetings = [
            m for m in meetings 
            if search_query in m['topic'].lower() or search_query in m['agenda'].lower()
        ]
        
    if not meetings:
        search_desc = f" matching '{args.search}'" if args.search else ""
        print(f"No meetings found between {start_dt.strftime('%Y-%m-%d')} and {end_dt.strftime('%Y-%m-%d')}{search_desc}.")
        sys.exit(0)
        
    search_desc = f" matching '{args.search}'" if args.search else ""
    print(f"### Zoom Meetings from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}{search_desc}\n")
    print("| Topic | Meeting ID | Occurrence UUID | Date / Time (UTC) | Type | Agenda |")
    print("|---|---|---|---|---|---|")
    for m in meetings:
        date_str = m['date'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"| {m['topic']} | {m['meeting_id']} | {m['uuid']} | {date_str} | {m['type']} | {m['agenda']} |")

if __name__ == '__main__':
    main()
