import os
import sys
import csv
import html
import argparse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import requests
from dotenv import load_dotenv, set_key

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
load_dotenv(dotenv_path)

FEEDS = {
    "Programmatic & CTV Industry Deals (Google News)": "https://news.google.com/rss/search?q=programmatic+OR+CTV+OR+%22Connected+TV%22+OR+%22ad+tech%22+OR+adtech+(partnership+OR+deal+OR+acquire+OR+merge+OR+partner+OR+launch)&hl=en-US&gl=US&ceid=US:en",
    "Digiday": "https://digiday.com/feed/",
    "AdExchanger": "https://www.adexchanger.com/feed/",
    "eMarketer": "https://news.google.com/rss/search?q=site:emarketer.com+OR+site:insiderintelligence.com&hl=en-US&gl=US&ceid=US:en",
    "Wall Street Journal (CMO Today)": "https://news.google.com/rss/search?q=site:wsj.com+%22CMO+Today%22+OR+site:wsj.com+%22marketing%22&hl=en-US&gl=US&ceid=US:en",
    "New York Times (Media & Advertising)": "https://rss.nytimes.com/services/xml/rss/nyt/MediaandAdvertising.xml",
    "NPR (Media & Tech)": "https://news.google.com/rss/search?q=site:npr.org+(%22marketing%22+OR+%22advertising%22+OR+%22programmatic%22+OR+%22media%22+OR+%22podcast%22)&hl=en-US&gl=US&ceid=US:en",
    "AdExchanger Talks Podcast": "https://adexchanger.libsyn.com/rss",
    "Marketecture Podcast": "https://marketecture.tv/feed/"
}

def fetch_feed(feed_name, url, days_limit):
    print(f"Fetching feed: {feed_name}...")
    articles = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days_limit)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        try:
            root = ET.fromstring(xml_data)
            channel = root.find('channel')
            if channel is None:
                return []
                
            for item in channel.findall('item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                desc_elem = item.find('description')
                
                title = html.unescape(title_elem.text) if title_elem is not None and title_elem.text else "No Title"
                link = link_elem.text if link_elem is not None and link_elem.text else ""
                pub_date_str = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else ""
                desc = html.unescape(desc_elem.text) if desc_elem is not None and desc_elem.text else ""
                
                # Clean up description HTML tags if any
                if desc:
                    # Simple HTML tag stripper
                    import re
                    desc = re.sub('<[^<]+?>', '', desc)
                    desc = desc.strip()
                    if len(desc) > 200:
                        desc = desc[:197] + "..."
                
                if pub_date_str:
                    try:
                        pub_date = parsedate_to_datetime(pub_date_str)
                        # Ensure pub_date is timezone-aware
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                    except Exception:
                        pub_date = None
                else:
                    pub_date = None
                    
                if pub_date and pub_date >= cutoff:
                    articles.append({
                        'title': title,
                        'link': link,
                        'pub_date': pub_date,
                        'source': feed_name,
                        'description': desc
                    })
        except ET.ParseError:
            # Fallback to BeautifulSoup for malformed XML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(xml_data, 'html.parser')
            for item in soup.find_all('item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                desc_elem = item.find('description')
                
                title = html.unescape(title_elem.text) if title_elem else "No Title"
                link = link_elem.text if link_elem else ""
                pub_date_str = pub_date_elem.text if pub_date_elem else ""
                desc = html.unescape(desc_elem.text) if desc_elem else ""
                
                if desc:
                    import re
                    desc = re.sub('<[^<]+?>', '', desc)
                    desc = desc.strip()
                    if len(desc) > 200:
                        desc = desc[:197] + "..."
                        
                if pub_date_str:
                    try:
                        pub_date = parsedate_to_datetime(pub_date_str)
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                    except Exception:
                        pub_date = None
                else:
                    pub_date = None
                    
                if pub_date and pub_date >= cutoff:
                    articles.append({
                        'title': title,
                        'link': link,
                        'pub_date': pub_date,
                        'source': feed_name,
                        'description': desc
                    })
                
    except Exception as e:
        print(f"Error fetching/parsing {feed_name}: {e}", file=sys.stderr)
        
    return articles

def refresh_slack_token(client_id, refresh_token):
    url = "https://slack.com/api/oauth.v2.access"
    data = {
        'client_id': client_id,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    client_secret = os.getenv('SLACK_CLIENT_SECRET')
    if client_secret:
        data['client_secret'] = client_secret
        
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        if token_data.get('ok'):
            new_access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token')
            if new_refresh_token:
                set_key(dotenv_path, 'SLACK_REFRESH_TOKEN', new_refresh_token)
                print("Successfully rotated SLACK_REFRESH_TOKEN in .env")
            return new_access_token
        else:
            error_msg = token_data.get('error', '')
            if 'invalid_refresh_token' in error_msg or 'invalid_grant' in error_msg:
                return refresh_token
            else:
                print(f"Error from Slack API during token refresh: {error_msg}")
                return None
    except Exception as e:
        print(f"Exception during token refresh: {e}")
        return None

def get_slack_user_id(name_or_email, access_token):
    clean_name = name_or_email.strip()
    # If it already looks like a Slack ID (starts with U, W, C, G) or a channel name (starts with #), return it directly
    if clean_name.startswith('#') or (len(clean_name) >= 9 and clean_name[0] in ('U', 'W', 'C', 'G') and clean_name[1:].isalnum()):
        return clean_name
        
    # Check cache first
    import json
    import time
    cache_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.slack_users_cache.json')
    members = []
    use_cache = False
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            # Cache is valid for 1 hour (3600 seconds)
            if time.time() - cache_data.get('timestamp', 0) < 3600:
                members = cache_data.get('members', [])
                use_cache = True
                print("Using cached Slack users list...")
        except Exception as e:
            print(f"Warning: Could not read Slack users cache: {e}")
            
    if not use_cache:
        url = "https://slack.com/api/users.list"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get('ok'):
                members = data.get('members', [])
                # Save to cache
                try:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump({'timestamp': time.time(), 'members': members}, f)
                    print("Successfully cached Slack users list.")
                except Exception as e:
                    print(f"Warning: Could not write Slack users cache: {e}")
            else:
                print(f"Warning: Could not fetch users list from Slack: {data.get('error')}")
                return clean_name
        except Exception as e:
            print(f"Exception fetching users list: {e}")
            return clean_name
            
    search_term = clean_name.lower().lstrip('@')
    for member in members:
        if member.get('deleted'):
            continue
            
        # Check username
        if (member.get('name') or '').lower() == search_term:
            return member['id']
            
        # Check real name
        if (member.get('real_name') or '').lower() == search_term:
            return member['id']
            
        # Check display name
        profile = member.get('profile', {})
        if (profile.get('display_name') or '').lower() == search_term:
            return member['id']
            
        # Check email
        if (profile.get('email') or '').lower() == search_term:
            return member['id']
            
    return clean_name

def open_dm_channel(user_id, access_token):
    url = "https://slack.com/api/conversations.open"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "users": user_id
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get('ok'):
            return data['channel']['id']
        else:
            print(f"Warning: Could not open DM channel with {user_id}: {data.get('error')}")
    except Exception as e:
        print(f"Exception opening DM channel with {user_id}: {e}")
    return user_id

def send_slack_message(channels, message):
    # Reload environment variables to get the latest rotated refresh token
    load_dotenv(dotenv_path, override=True)
    refresh_token_env = os.getenv('SLACK_REFRESH_TOKEN')
    client_id = os.getenv('SLACK_CLIENT_ID')
    
    if not refresh_token_env or not client_id:
        print("Warning: Missing SLACK_REFRESH_TOKEN or SLACK_CLIENT_ID in .env. Skipping Slack notification.")
        return
        
    if refresh_token_env.startswith("xoxp-") or refresh_token_env.startswith("xoxe.xoxp-") or refresh_token_env.startswith("xoxb-"):
        access_token = refresh_token_env
    else:
        access_token = refresh_slack_token(client_id, refresh_token_env)
        
    if not access_token:
        print("Warning: Could not obtain a valid Slack access token. Skipping Slack notification.")
        return
        
    post_url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Split channels by comma and strip whitespace
    target_list = [c.strip() for c in channels.split(',') if c.strip()]
    
    for target in target_list:
        # Resolve user ID if it's a name or email
        resolved_target = get_slack_user_id(target, access_token)
        
        # If it's a user ID (starts with U or W), open a DM channel first
        if resolved_target.startswith('U') or resolved_target.startswith('W'):
            post_target = open_dm_channel(resolved_target, access_token)
        else:
            post_target = resolved_target
            
        payload = {
            "channel": post_target,
            "text": message,
            "as_user": True
        }
        
        try:
            response = requests.post(post_url, headers=headers, json=payload)
            response.raise_for_status()
            res_data = response.json()
            if res_data.get('ok'):
                print(f"Successfully sent summary to Slack target {post_target} ({target})!")
            else:
                print(f"Failed to send Slack message to {post_target} ({target}): {res_data.get('error')}")
        except Exception as e:
            print(f"Exception sending Slack message to {post_target} ({target}): {e}")

def setup_schedule(days, output_dir, slack_channel, sources, max_articles, interval):
    if sys.platform != 'darwin':
        print("Scheduling is currently only supported on macOS via launchd.")
        return
        
    home = os.path.expanduser('~')
    launch_agents_dir = os.path.join(home, 'Library', 'LaunchAgents')
    os.makedirs(launch_agents_dir, exist_ok=True)
    
    plist_path = os.path.join(launch_agents_dir, 'com.user.programmatic-news-fetch.plist')
    
    # Get absolute paths
    script_path = os.path.abspath(__file__)
    abs_output_dir = os.path.abspath(output_dir)
    python_bin = sys.executable
    
    args_list = [
        python_bin,
        script_path,
        '--days', str(days),
        '--output-dir', abs_output_dir,
        '--sources', sources,
        '--max-articles', str(max_articles)
    ]
    if slack_channel:
        args_list.extend(['--slack-channel', slack_channel])
        
    args_xml = "".join(f"        <string>{html.escape(arg)}</string>\n" for arg in args_list)
    
    # Schedule to run every Tuesday at 9:00 AM
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.programmatic-news-fetch</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>2</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{html.escape(os.path.join(abs_output_dir, 'programmatic_news_fetch.log'))}</string>
    <key>StandardErrorPath</key>
    <string>{html.escape(os.path.join(abs_output_dir, 'programmatic_news_fetch_err.log'))}</string>
</dict>
</plist>
"""
    with open(plist_path, 'w', encoding='utf-8') as f:
        f.write(plist_content)
        
    print(f"Successfully created launchd plist at {plist_path}")
    
    # Load the plist
    import subprocess
    try:
        # Unload first if already loaded
        subprocess.run(['launchctl', 'unload', plist_path], capture_output=True)
        result = subprocess.run(['launchctl', 'load', plist_path], capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully scheduled programmatic-news-fetch to run every Tuesday at 9:00 AM!")
        else:
            print(f"Warning: Could not load plist with launchctl: {result.stderr}")
    except Exception as e:
        print(f"Error loading plist: {e}")

def get_programmatic_news(days=7, sources="deals,digiday,adexchanger,emarketer,wsj,nyt,npr,podcasts", max_articles=20, strict_filter=True):
    source_map = {
        "deals": "Programmatic & CTV Industry Deals (Google News)",
        "digiday": "Digiday",
        "adexchanger": "AdExchanger",
        "emarketer": "eMarketer",
        "wsj": "Wall Street Journal (CMO Today)",
        "nyt": "New York Times (Media & Advertising)",
        "npr": "NPR (Media & Tech)",
        "podcasts": ["AdExchanger Talks Podcast", "Marketecture Podcast"]
    }
    
    selected_sources = [s.strip().lower() for s in sources.split(',')]
    active_feeds = {}
    for s in selected_sources:
        if s in source_map:
            names = source_map[s]
            if isinstance(names, list):
                for name in names:
                    if name in FEEDS:
                        active_feeds[name] = FEEDS[name]
            else:
                if names in FEEDS:
                    active_feeds[names] = FEEDS[names]
            
    if not active_feeds:
        return []
        
    all_articles = []
    for name, url in active_feeds.items():
        all_articles.extend(fetch_feed(name, url, days))
        
    # Deduplicate articles by title or link
    seen_titles = set()
    seen_links = set()
    unique_articles = []
    
    for art in all_articles:
        title_norm = art['title'].lower().strip()
        link_norm = art['link'].lower().strip()
        if title_norm not in seen_titles and link_norm not in seen_links:
            seen_titles.add(title_norm)
            seen_links.add(link_norm)
            unique_articles.append(art)
            
    # Sort articles by publication date descending
    unique_articles.sort(key=lambda x: x['pub_date'] if x['pub_date'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    
    if not strict_filter:
        return unique_articles[:max_articles]
    
    # Filter for Programmatic and CTV focused articles
    FOCUS_KEYWORDS = [
        "programmatic", "ctv", "connected tv", "ott", "streaming", "ad tech", "adtech", 
        "bidding", "dsp", "ssp", "rtb", "header bidding", "magnite", "pubmatic", 
        "the trade desk", "ttd", "dv360", "viasat", "pause ads", "ad fraud", "attention metrics",
        "retail media", "first-party data", "identity", "privacy", "cookie", "clean room", 
        "targeting", "measurement", "attribution", "spotify", "apple", "major league soccer", 
        "mls", "streaming service", "partnership", "deal", "launch", "podcast", "digital marketing",
        "marketing", "advertising", "brand media", "integrated media", "brand safety", 
        "brand suitability", "sponsorship", "brand integration", "creator economy", "influencer", 
        "native advertising", "omnichannel", "cross-channel", "brand lift", "brand awareness", 
        "media planning", "media buying", "media mix"
    ]
    
    focused_articles = []
    TRUSTED_DOMAINS = ["digiday.com", "adexchanger.com", "emarketer.com", "insiderintelligence.com", "wsj.com", "nytimes.com", "adweek.com", "npr.org", "libsyn.com", "buzzsprout.com"]
    import re
    
    for art in unique_articles:
        text_to_check = (art['title'] + " " + art['description']).lower()
        
        # Match keywords with word boundaries to avoid false positives (e.g. "heartbreaking" matching "rtb")
        has_keyword = False
        for kw in FOCUS_KEYWORDS:
            # Use word boundaries for short acronyms or all keywords
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, text_to_check):
                has_keyword = True
                break
                
        if has_keyword:
            # Check if the article is from a trusted, objective domain
            link_lower = art['link'].lower()
            is_trusted = False
            for domain in TRUSTED_DOMAINS:
                if domain in link_lower:
                    is_trusted = True
                    break
            
            # Also check the source name
            source_lower = art['source'].lower()
            for domain in TRUSTED_DOMAINS:
                name_part = domain.split('.')[0]
                if name_part in source_lower:
                    is_trusted = True
                    break
                    
            # For Google News items, the source is often in the title suffix, e.g., " - ADWEEK"
            if " - " in art['title']:
                suffix = art['title'].split(" - ")[-1].lower()
                for domain in TRUSTED_DOMAINS:
                    name_part = domain.split('.')[0]
                    if name_part in suffix:
                        is_trusted = True
                        break
                        
            if is_trusted:
                focused_articles.append(art)
                
    return focused_articles[:max_articles]

def main():
    parser = argparse.ArgumentParser(description="Fetch programmatic news articles from RSS feeds")
    parser.add_argument('--days', type=int, default=7, help="Number of days of news to fetch (default: 7)")
    parser.add_argument('--output-dir', type=str, default=".", help="Directory to save reports (default: current directory)")
    parser.add_argument('--slack-channel', type=str, help="Optional Slack channel to send the summary report to")
    parser.add_argument('--schedule', action='store_true', help="Schedule this script to run automatically via launchd")
    parser.add_argument('--sources', type=str, default="deals,digiday,adexchanger,emarketer,wsj,nyt,npr,podcasts", help="Comma-separated list of sources to fetch (options: deals, digiday, adexchanger, emarketer, wsj, nyt, npr, podcasts; default: deals,digiday,adexchanger,emarketer,wsj,nyt,npr,podcasts)")
    parser.add_argument('--max-articles', type=int, default=20, help="Maximum number of articles to include in the report (default: 20)")
    parser.add_argument('--interval', type=int, default=604800, help="Interval in seconds for the scheduled task (default: 604800 / 7 days)")
    
    args = parser.parse_args()
    
    if args.schedule:
        setup_schedule(args.days, args.output_dir, args.slack_channel, args.sources, args.max_articles, args.interval)
        return
        
    unique_articles = get_programmatic_news(args.days, args.sources, args.max_articles)
    
    if not unique_articles:
        print(f"No programmatic or CTV focused news articles found from trusted sources in the last {args.days} days.")
        return
        
    print(f"Found {len(unique_articles)} focused articles from trusted sources.")
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate Markdown Report
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_filename = f"programmatic_news_report_{date_str}.md"
    md_path = os.path.join(args.output_dir, md_filename)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Programmatic Industry News Report\n")
        f.write(f"**Date:** {datetime.now().strftime('%B %d, %Y')} | **Timeframe:** Last {args.days} Days\n\n")
        f.write(f"Here is a curated list of the latest news and updates from the programmatic advertising industry to share with your client.\n\n")
        
        f.write("## Summary Table\n\n")
        f.write("| Date | Source | Title | Link |\n")
        f.write("| --- | --- | --- | --- |\n")
        for art in unique_articles:
            pub_date_formatted = art['pub_date'].strftime('%Y-%m-%d') if art['pub_date'] else "N/A"
            # Clean title for markdown table
            clean_title = art['title'].replace('|', '\\|')
            f.write(f"| {pub_date_formatted} | {art['source']} | {clean_title} | [Link]({art['link']}) |\n")
            
        f.write("\n## Article Details\n\n")
        for i, art in enumerate(unique_articles, 1):
            pub_date_formatted = art['pub_date'].strftime('%B %d, %Y') if art['pub_date'] else "N/A"
            f.write(f"### {i}. {art['title']}\n")
            f.write(f"- **Source:** {art['source']}\n")
            f.write(f"- **Published:** {pub_date_formatted}\n")
            f.write(f"- **URL:** {art['link']}\n")
            if art['description']:
                f.write(f"- **Snippet:** {art['description']}\n")
            f.write("\n---\n\n")
            
    print(f"Saved Markdown report to {md_path}")
    
    # Generate CSV Report
    csv_filename = f"programmatic_news_report_{date_str}.csv"
    csv_path = os.path.join(args.output_dir, csv_filename)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Source', 'Title', 'URL', 'Snippet'])
        for art in unique_articles:
            pub_date_formatted = art['pub_date'].strftime('%Y-%m-%d') if art['pub_date'] else "N/A"
            writer.writerow([pub_date_formatted, art['source'], art['title'], art['link'], art['description']])
            
    print(f"Saved CSV report to {csv_path}")
    
    # Send Slack Notification if requested
    if args.slack_channel:
        slack_msg = f"📰 *Programmatic Industry News Report - {datetime.now().strftime('%B %d, %Y')}*\n"
        slack_msg += f"Here are the top programmatic news articles from the last {args.days} days:\n\n"
        for i, art in enumerate(unique_articles[:5], 1):
            slack_msg += f"{i}. *<{art['link']}|{art['title']}>* ({art['source']})\n"
        if len(unique_articles) > 5:
            slack_msg += f"\n_...and {len(unique_articles) - 5} more articles in the full report._\n"
        slack_msg += f"\nReports saved locally:\n- `{md_filename}`\n- `{csv_filename}`"
        send_slack_message(args.slack_channel, slack_msg)

if __name__ == '__main__':
    main()