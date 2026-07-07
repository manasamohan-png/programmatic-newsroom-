import os
import sys
import glob
import csv
import re
import json
from datetime import datetime, timezone
import streamlit as st

# Set page configuration (MUST be the very first Streamlit command)
st.set_page_config(
    page_title="Programmatic & CTV Newsroom",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the scripts directory to sys.path so we can import fetch_news
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".agents", "skills", "programmatic-news-fetch", "scripts"))
sys.path.append(scripts_dir)
try:
    import fetch_news
except ImportError as e:
    st.error(f"Could not import fetch_news.py. Error: {e}. Path checked: {scripts_dir}")

# Custom CSS for a premium, modern news website look (Slate, Indigo, and clean grid cards)
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
        font-size: 16px;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #4f46e5 !important;
        color: #4f46e5 !important;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: white;
        padding: 40px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-bottom: 4px solid #4f46e5;
    }
    
    /* Article Cards Grid */
    .news-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
        gap: 24px;
        margin-bottom: 30px;
    }
    
    .article-card {
        background-color: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    .article-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.08);
        border-color: #cbd5e1;
    }
    .article-card-selected {
        border-left: 5px solid #4f46e5;
    }
    
    /* Featured Article Card */
    .featured-card {
        background-color: white;
        padding: 32px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        border-left: 6px solid #4f46e5;
        margin-bottom: 30px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .featured-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.08);
    }
    
    /* Badges */
    .source-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        margin-right: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-digiday { background-color: #fee2e2; color: #991b1b; }
    .badge-adexchanger { background-color: #dbeafe; color: #1e40af; }
    .badge-emarketer { background-color: #d1fae5; color: #065f46; }
    .badge-wsj { background-color: #fef3c7; color: #92400e; }
    .badge-nyt { background-color: #f3e8ff; color: #6b21a8; }
    .badge-npr { background-color: #e0f2fe; color: #0369a1; }
    .badge-podcast { background-color: #fae8ff; color: #86198f; }
    .badge-deals { background-color: #f1f5f9; color: #334155; }
    .badge-custom { background-color: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    
    /* Channel Badges */
    .channel-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        margin-right: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .channel-programmatic { background-color: #e0e7ff; color: #4338ca; }
    .channel-brand { background-color: #d1fae5; color: #047857; }
    .channel-integrated { background-color: #fef3c7; color: #d97706; }
    
    .article-title {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
        text-decoration: none;
        margin-top: 12px;
        margin-bottom: 12px;
        display: block;
        line-height: 1.4;
    }
    .article-title:hover {
        color: #4f46e5;
    }
    .featured-title {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        text-decoration: none;
        margin-top: 12px;
        margin-bottom: 12px;
        display: block;
        line-height: 1.3;
    }
    .featured-title:hover {
        color: #4f46e5;
    }
    .article-meta {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .article-snippet {
        font-size: 14px;
        color: #334155;
        line-height: 1.6;
        margin-bottom: 16px;
    }
    
    /* Strategic Boxes */
    .insight-box {
        background-color: #fffbe6;
        border: 1px solid #ffe58f;
        padding: 16px;
        border-radius: 8px;
        margin-top: 16px;
        margin-bottom: 16px;
    }
    .insight-title {
        font-weight: 700;
        color: #d46b08;
        font-size: 13px;
        text-transform: uppercase;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    .app-box {
        background-color: #f6ffed;
        border: 1px solid #b7eb8f;
        padding: 16px;
        border-radius: 8px;
        margin-top: 12px;
        margin-bottom: 12px;
    }
    .app-title {
        font-weight: 700;
        color: #389e0d;
        font-size: 13px;
        text-transform: uppercase;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

def get_badge_class(source_name):
    name = source_name.lower()
    if "digiday" in name:
        return "badge-digiday"
    elif "adexchanger" in name:
        return "badge-adexchanger"
    elif "emarketer" in name or "insider" in name:
        return "badge-emarketer"
    elif "wall street" in name or "wsj" in name:
        return "badge-wsj"
    elif "new york times" in name or "nyt" in name:
        return "badge-nyt"
    elif "npr" in name:
        return "badge-npr"
    elif "podcast" in name:
        return "badge-podcast"
    elif "custom" in name or "top of mind" in name:
        return "badge-custom"
    else:
        return "badge-deals"

def classify_channel(title, description):
    text = (title + " " + description).lower()
    
    programmatic_kws = [
        "programmatic", "ctv", "connected tv", "dsp", "ssp", "rtb", "bidding", 
        "ad tech", "adtech", "the trade desk", "ttd", "dv360", "magnite", "pubmatic", 
        "cookie", "privacy", "clean room", "targeting", "measurement", "attribution", "ad fraud"
    ]
    
    brand_kws = [
        "brand safety", "brand suitability", "sponsorship", "brand integration", 
        "brand lift", "brand awareness", "spotify", "apple", "streaming service", 
        "partnership", "deal", "launch", "podcast", "advertising", "marketing", "brand media"
    ]
    
    integrated_kws = [
        "integrated media", "omnichannel", "cross-channel", "media planning", 
        "media buying", "media mix", "creator economy", "influencer", "native advertising", 
        "content marketing"
    ]
    
    prog_score = sum(1 for kw in programmatic_kws if kw in text)
    brand_score = sum(1 for kw in brand_kws if kw in text)
    int_score = sum(1 for kw in integrated_kws if kw in text)
    
    if prog_score == 0 and brand_score == 0 and int_score == 0:
        return "Programmatic"
        
    max_score = max(prog_score, brand_score, int_score)
    if max_score == prog_score:
        return "Programmatic"
    elif max_score == brand_score:
        return "Brand Media"
    else:
        return "Integrated Media"

def get_channel_badge_class(channel_name):
    name = channel_name.lower()
    if "programmatic" in name:
        return "channel-programmatic"
    elif "brand" in name:
        return "channel-brand"
    else:
        return "channel-integrated"

def load_agenda_state():
    """Load the saved agenda state from JSON, falling back to the latest CSV report."""
    if os.path.exists("news_agenda.json"):
        try:
            with open("news_agenda.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                articles = data.get("articles", [])
                custom_items = data.get("custom_items", [])
                
                # Parse dates
                for art in articles:
                    if art.get("pub_date"):
                        try:
                            art["pub_date"] = datetime.strptime(art["pub_date"], "%Y-%m-%d")
                        except ValueError:
                            art["pub_date"] = None
                for item in custom_items:
                    if item.get("pub_date"):
                        try:
                            item["pub_date"] = datetime.strptime(item["pub_date"], "%Y-%m-%d")
                        except ValueError:
                            item["pub_date"] = None
                return articles, custom_items
        except Exception as e:
            st.error(f"Error loading agenda state: {e}")
            
    # Fallback to old kohler file if it exists
    if os.path.exists("kohler_news_agenda.json"):
        try:
            with open("kohler_news_agenda.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                articles = data.get("articles", [])
                custom_items = data.get("custom_items", [])
                for art in articles:
                    if art.get("pub_date"):
                        try:
                            art["pub_date"] = datetime.strptime(art["pub_date"], "%Y-%m-%d")
                        except ValueError:
                            art["pub_date"] = None
                for item in custom_items:
                    if item.get("pub_date"):
                        try:
                            item["pub_date"] = datetime.strptime(item["pub_date"], "%Y-%m-%d")
                        except ValueError:
                            item["pub_date"] = None
                return articles, custom_items
        except Exception:
            pass
            
    # Fallback to CSV
    csv_files = glob.glob("programmatic_news_report_*.csv")
    if not csv_files:
        return [], []
    
    csv_files.sort(reverse=True)
    latest_file = csv_files[0]
    
    articles = []
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pub_date = None
                if row.get('Date') and row['Date'] != 'N/A':
                    try:
                        pub_date = datetime.strptime(row['Date'], '%Y-%m-%d')
                    except ValueError:
                        pass
                
                articles.append({
                    'title': row.get('Title', 'No Title'),
                    'link': row.get('URL', ''),
                    'pub_date': pub_date,
                    'source': row.get('Source', 'Unknown'),
                    'description': row.get('Snippet', ''),
                    'insight': '',
                    'app_brand': '',
                    'app_agency': '',
                    'channel': classify_channel(row.get('Title', ''), row.get('Snippet', '')),
                    'selected': True
                })
    except Exception as e:
        st.error(f"Error loading latest report: {e}")
        
    return articles, []

def save_agenda_state(articles, custom_items):
    """Save the current agenda state to JSON and generate Markdown/CSV reports."""
    # Serialize dates for JSON
    serialized_articles = []
    for art in articles:
        art_copy = art.copy()
        if isinstance(art_copy.get('pub_date'), datetime):
            art_copy['pub_date'] = art_copy['pub_date'].strftime('%Y-%m-%d')
        serialized_articles.append(art_copy)
        
    serialized_custom = []
    for item in custom_items:
        item_copy = item.copy()
        if isinstance(item_copy.get('pub_date'), datetime):
            item_copy['pub_date'] = item_copy['pub_date'].strftime('%Y-%m-%d')
        serialized_custom.append(item_copy)
        
    state_data = {
        "articles": serialized_articles,
        "custom_items": serialized_custom
    }
    
    try:
        with open("news_agenda.json", "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=4)
            
        # Also save standard reports for backward compatibility and easy sharing
        date_str = datetime.now().strftime("%Y-%m-%d")
        md_filename = f"programmatic_news_report_{date_str}.md"
        csv_filename = f"programmatic_news_report_{date_str}.csv"
        
        # Filter selected items
        selected_articles = [a for a in articles if a.get('selected', True)]
        selected_custom = [c for c in custom_items if c.get('selected', True)]
        all_selected = selected_custom + selected_articles
        
        # Save Markdown
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Programmatic & CTV News Agenda\n")
            f.write(f"**Date:** {datetime.now().strftime('%B %d, %Y')} | **Timeframe:** Last Week\n\n")
            f.write(f"Curated strategic insights and opportunities from the programmatic and brand media landscape.\n\n")
            
            f.write("## Summary Table\n\n")
            f.write("| Date | Source | Title | Link |\n")
            f.write("| --- | --- | --- | --- |\n")
            for art in all_selected:
                pub_date_formatted = art['pub_date'].strftime('%Y-%m-%d') if art['pub_date'] else "N/A"
                clean_title = art['title'].replace('|', '\\|')
                link_str = f"[Link]({art['link']})" if art['link'] else "N/A"
                f.write(f"| {pub_date_formatted} | {art['source']} | {clean_title} | {link_str} |\n")
                
            f.write("\n## Strategic Insights & Applications\n\n")
            for i, art in enumerate(all_selected, 1):
                pub_date_formatted = art['pub_date'].strftime('%B %d, %Y') if art['pub_date'] else "N/A"
                f.write(f"### {i}. {art['title']}\n")
                f.write(f"- **Source:** {art['source']} | **Published:** {pub_date_formatted} | **Channel:** {art.get('channel', 'Programmatic')}\n")
                if art['link']:
                    f.write(f"- **URL:** {art['link']}\n")
                if art['description']:
                    f.write(f"- **Snippet:** {art['description']}\n")
                if art.get('insight'):
                    f.write(f"- **Strategic Insight:** {art['insight']}\n")
                if art.get('app_brand'):
                    f.write(f"- **Application for Brand Team:** {art['app_brand']}\n")
                if art.get('app_agency'):
                    f.write(f"- **Application for Agency Team:** {art['app_agency']}\n")
                f.write("\n---\n\n")
                
        # Save CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Source', 'Title', 'URL', 'Snippet', 'Insight', 'Application Brand', 'Application Agency', 'Channel'])
            for art in all_selected:
                pub_date_formatted = art['pub_date'].strftime('%Y-%m-%d') if art['pub_date'] else "N/A"
                writer.writerow([
                    pub_date_formatted, 
                    art['source'], 
                    art['title'], 
                    art['link'], 
                    art['description'],
                    art.get('insight', ''),
                    art.get('app_brand', ''),
                    art.get('app_agency', ''),
                    art.get('channel', 'Programmatic')
                ])
                
        return True
    except Exception as e:
        st.error(f"Error saving agenda state: {e}")
        return False

# Initialize session state
if 'articles' not in st.session_state or 'custom_items' not in st.session_state:
    articles, custom_items = load_agenda_state()
    # Map old keys to new keys if loading old state
    for art in articles:
        if 'app_kohler' in art:
            art['app_brand'] = art.pop('app_kohler')
        if 'app_pmg' in art:
            art['app_agency'] = art.pop('app_pmg')
        if 'app_brand' not in art:
            art['app_brand'] = ''
        if 'app_agency' not in art:
            art['app_agency'] = ''
        if 'channel' not in art:
            art['channel'] = classify_channel(art.get('title', ''), art.get('description', ''))
            
    for item in custom_items:
        if 'app_kohler' in item:
            item['app_brand'] = item.pop('app_kohler')
        if 'app_pmg' in item:
            item['app_agency'] = item.pop('app_pmg')
        if 'app_brand' not in item:
            item['app_brand'] = ''
        if 'app_agency' not in item:
            item['app_agency'] = ''
        if 'channel' not in item:
            item['channel'] = classify_channel(item.get('title', ''), item.get('description', ''))
            
    st.session_state.articles = articles
    st.session_state.custom_items = custom_items
    st.session_state.last_loaded = "Loaded from local cache" if articles else "No articles loaded yet"

# Sidebar
st.sidebar.header("⚙️ Newsroom Settings")

days_to_fetch = st.sidebar.slider("Days of news to fetch", min_value=1, max_value=30, value=7, help="Select the timeframe for news updates.")
if days_to_fetch > 7:
    st.sidebar.warning("⚠️ Timeframes longer than 7 days may include less relevant news.")

max_articles = st.sidebar.slider("Max articles to display", min_value=5, max_value=50, value=15)

strict_filter = st.sidebar.checkbox("Strict Programmatic Filter", value=True, help="Only show articles matching programmatic, CTV, and privacy keywords.")
if not strict_filter:
    st.sidebar.info("💡 Showing all premium news. You can find insights to connect general media news to programmatic manually.")

source_options = {
    "deals": "Programmatic & CTV Industry Deals (Google News)",
    "digiday": "Digiday",
    "adexchanger": "AdExchanger",
    "emarketer": "eMarketer",
    "wsj": "Wall Street Journal (CMO Today)",
    "nyt": "New York Times (Media & Advertising)",
    "npr": "NPR (Media & Tech)",
    "podcasts": "Ad Tech & Marketing Podcasts"
}

selected_sources = st.sidebar.multiselect(
    "Sources to include",
    options=list(source_options.keys()),
    default=list(source_options.keys()),
    format_func=lambda x: source_options[x]
)

if st.sidebar.button("🔄 Fetch Latest News", type="primary", use_container_width=True):
    if not selected_sources:
        st.sidebar.error("Please select at least one source.")
    else:
        with st.spinner("Fetching and filtering premium feeds..."):
            sources_str = ",".join(selected_sources)
            try:
                # Fetch news using the refactored function with strict_filter parameter
                fetched = fetch_news.get_programmatic_news(
                    days=days_to_fetch,
                    sources=sources_str,
                    max_articles=max_articles,
                    strict_filter=strict_filter
                )
                
                if fetched:
                    # Merge with existing articles to preserve edits if titles match
                    existing_by_title = {a['title'].lower().strip(): a for a in st.session_state.articles}
                    
                    merged_articles = []
                    for art in fetched:
                        title_norm = art['title'].lower().strip()
                        if title_norm in existing_by_title:
                            # Keep existing edits
                            merged_articles.append(existing_by_title[title_norm])
                        else:
                            # Add new article with empty fields and auto-classification
                            art['insight'] = ''
                            art['app_brand'] = ''
                            art['app_agency'] = ''
                            art['channel'] = classify_channel(art.get('title', ''), art.get('description', ''))
                            art['selected'] = True
                            merged_articles.append(art)
                            
                    st.session_state.articles = merged_articles
                    st.session_state.last_loaded = f"Freshly fetched at {datetime.now().strftime('%H:%M:%S')}"
                    save_agenda_state(st.session_state.articles, st.session_state.custom_items)
                    st.sidebar.success(f"Successfully fetched {len(fetched)} articles!")
                else:
                    st.sidebar.warning("No articles found matching the criteria.")
            except Exception as e:
                st.sidebar.error(f"Error fetching news: {e}")

# Add Custom Agenda Item Section
st.sidebar.markdown("---")
st.sidebar.header("➕ Add Custom News / Topic")
st.sidebar.info("Add custom articles, podcast episodes, or topics that weren't captured in the RSS feeds.")

with st.sidebar.form("custom_item_form", clear_on_submit=True):
    custom_title = st.text_input("Title", placeholder="e.g., New Privacy Sandbox Updates")
    custom_source = st.text_input("Source", value="Custom / Podcast")
    custom_desc = st.text_area("Description / Notes", placeholder="Brief details about the topic...")
    custom_channel = st.selectbox("Channel Tag", options=["Programmatic", "Brand Media", "Integrated Media"])
    
    submit_custom = st.form_submit_button("Add to Newsroom", use_container_width=True)
    if submit_custom and custom_title:
        new_item = {
            "title": custom_title,
            "source": custom_source,
            "pub_date": datetime.now(),
            "description": custom_desc,
            "insight": "",
            "app_brand": "",
            "app_agency": "",
            "channel": custom_channel,
            "selected": True
        }
        st.session_state.custom_items.append(new_item)
        save_agenda_state(st.session_state.articles, st.session_state.custom_items)
        st.sidebar.success("Added custom item!")

# Slack Notification Section
st.sidebar.markdown("---")
st.sidebar.header("💬 Slack Notification")
slack_channels = st.sidebar.text_input(
    "Slack Channels", 
    value="#general", 
    help="Enter comma-separated channels (e.g. #general, #marketing)."
)
slack_users = st.sidebar.text_input(
    "Slack Users (Direct Message)", 
    value="", 
    help="Enter comma-separated display names, real names, emails, or Slack User IDs (e.g. John Doe, john@company.com, U12345678)."
)

if st.sidebar.button("📤 Send Report to Slack", use_container_width=True):
    selected_articles = [a for a in st.session_state.articles if a.get('selected', True)]
    selected_custom = [c for c in st.session_state.custom_items if c.get('selected', True)]
    all_selected = selected_custom + selected_articles
    
    if not all_selected:
        st.sidebar.error("No selected articles to send. Please select or fetch news first.")
    elif not slack_channels.strip() and not slack_users.strip():
        st.sidebar.error("Please enter at least one channel or user.")
    else:
        with st.spinner("Sending to Slack..."):
            try:
                slack_msg = f"📰 *Programmatic & CTV News Agenda - {datetime.now().strftime('%B %d, %Y')}*\n"
                slack_msg += f"Here is the curated news agenda for our upcoming call:\n\n"
                for i, art in enumerate(all_selected[:5], 1):
                    link_part = f"<{art['link']}|{art['title']}>" if art['link'] else art['title']
                    slack_msg += f"{i}. *{link_part}* ({art['source']})\n"
                    if art.get('insight'):
                        slack_msg += f"   _Insight:_ {art['insight']}\n"
                if len(all_selected) > 5:
                    slack_msg += f"\n_...and {len(all_selected) - 5} more items in the full agenda._\n"
                
                # Combine targets
                targets = []
                if slack_channels.strip():
                    targets.append(slack_channels.strip())
                if slack_users.strip():
                    targets.append(slack_users.strip())
                combined_targets = ", ".join(targets)
                
                fetch_news.send_slack_message(combined_targets, slack_msg)
                st.sidebar.success(f"Sent to Slack targets: {combined_targets}!")
            except Exception as e:
                st.sidebar.error(f"Error sending to Slack: {e}")

# Main Panel Content
# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 style="color: white; margin: 0; font-size: 36px; font-weight: 800; letter-spacing: -0.5px;">Programmatic & CTV Newsroom</h1>
    <p style="color: #94a3b8; margin: 10px 0 0 0; font-size: 18px; font-weight: 500;">
        A premium, curated feed of the latest programmatic advertising, Connected TV (CTV), consumer privacy, brand, and integrated media updates.
    </p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["📰 Curated Newsroom", "📊 Presentation Mode", "📥 Export & Download"])

# Quick Insight Templates
INSIGHT_TEMPLATES = {
    "Cookie Deprecation / Privacy": "With consumer privacy and cookie deprecation top of mind, this highlights the growing importance of first-party data and clean room solutions for targeting.",
    "CTV / Streaming Growth": "As streaming services expand their ad-supported tiers, this presents new premium CTV inventory opportunities to reach engaged audiences.",
    "DSP / SSP Innovation": "This new feature/partnership allows for more precise show-level targeting and performance optimization within DSP campaigns.",
    "Brand Media Shift": "While not strictly programmatic, this media landscape shift offers a unique brand integration opportunity that can be explored via programmatic private marketplace (PMP) deals.",
    "Brand / Integrated Media": "This brand/integrated media update highlights a unique opportunity to align programmatic campaigns with broader cross-channel sponsorships and native integrations."
}

with tab1:
    # Search and Filter Bar
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔍 Search articles", placeholder="Type keywords to filter...")
    with col2:
        all_sources = list(set(art['source'] for art in st.session_state.articles)) + list(set(item['source'] for item in st.session_state.custom_items))
        available_sources = sorted(list(set(all_sources)))
        selected_filter_sources = st.multiselect("Filter by Source", options=available_sources, default=available_sources)

    # Filter articles and custom items
    filtered_articles = []
    for art in st.session_state.articles:
        if art['source'] not in selected_filter_sources:
            continue
        if search_query:
            q = search_query.lower()
            if q not in art['title'].lower() and q not in art['description'].lower() and art['source'].lower():
                continue
        filtered_articles.append(art)
        
    filtered_custom = []
    for item in st.session_state.custom_items:
        if item['source'] not in selected_filter_sources:
            continue
        if search_query:
            q = search_query.lower()
            if q not in item['title'].lower() and q not in item['description'].lower() and item['source'].lower():
                continue
        filtered_custom.append(item)

    all_items = filtered_custom + filtered_articles

    if not all_items:
        st.info("No articles match your search or filter criteria.")
    else:
        # Display Featured Article (the first selected item)
        featured_item = None
        for item in all_items:
            if item.get('selected', True):
                featured_item = item
                break
                
        if featured_item:
            st.markdown("### 🌟 Featured Story")
            badge_class = get_badge_class(featured_item['source'])
            channel_badge_class = get_channel_badge_class(featured_item.get('channel', 'Programmatic'))
            pub_date_str = featured_item['pub_date'].strftime('%B %d, %Y') if featured_item['pub_date'] else "N/A"
            link_html = f'href="{featured_item["link"]}" target="_blank"' if featured_item.get('link') else ''
            
            st.markdown(f"""
            <div class="featured-card">
                <div>
                    <span class="source-badge {badge_class}">{featured_item['source']}</span>
                    <span class="channel-badge {channel_badge_class}">{featured_item.get('channel', 'Programmatic')}</span>
                    <span style="font-size: 13px; color: #64748b;">📅 {pub_date_str}</span>
                </div>
                <a {link_html} class="featured-title">{featured_item['title']}</a>
                <div class="article-snippet" style="font-size: 16px;">{featured_item['description'] if featured_item['description'] else "No description available."}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Expander for editing featured article
            with st.expander("✍️ Add Strategic Insights & Applications", expanded=False):
                featured_item['selected'] = st.checkbox("Include in Presentation", value=featured_item.get('selected', True), key="sel_featured")
                
                # Channel override selectbox
                channel_options = ["Programmatic", "Brand Media", "Integrated Media"]
                try:
                    channel_idx = channel_options.index(featured_item.get('channel', 'Programmatic'))
                except ValueError:
                    channel_idx = 0
                featured_item['channel'] = st.selectbox("Channel Tag", options=channel_options, index=channel_idx, key="chan_featured")
                
                st.markdown("**Quick Insight Templates:**")
                cols = st.columns(len(INSIGHT_TEMPLATES))
                for c_idx, (template_name, template_text) in enumerate(INSIGHT_TEMPLATES.items()):
                    if cols[c_idx].button(template_name, key=f"tpl_featured_{c_idx}"):
                        featured_item['insight'] = template_text
                        save_agenda_state(st.session_state.articles, st.session_state.custom_items)
                        st.rerun()
                        
                featured_item['insight'] = st.text_area(
                    "Strategic Insight / Connection to Programmatic", 
                    value=featured_item.get('insight', ''), 
                    placeholder="Find an insight to connect this to programmatic or brand media...",
                    key="ins_featured"
                )
                featured_item['app_brand'] = st.text_area(
                    "Application for Brand Team", 
                    value=featured_item.get('app_brand', ''), 
                    placeholder="How the brand/client team can leverage this opportunity...",
                    key="app_b_featured"
                )
                featured_item['app_agency'] = st.text_area(
                    "Application for Agency Team", 
                    value=featured_item.get('app_agency', ''), 
                    placeholder="How the agency/media team will execute, test, or monitor this...",
                    key="app_a_featured"
                )
                if st.button("💾 Save Featured Edits", key="save_featured"):
                    save_agenda_state(st.session_state.articles, st.session_state.custom_items)
                    st.success("Saved!")
            st.markdown("<br>", unsafe_allow_html=True)

        # Display the rest of the articles in a beautiful grid
        st.markdown("### 📰 Latest Updates")
        
        # We will render the grid using Streamlit columns
        cols_per_row = 2
        for i in range(0, len(all_items), cols_per_row):
            row_items = all_items[i:i+cols_per_row]
            cols = st.columns(cols_per_row)
            
            for idx, item in enumerate(row_items):
                global_idx = i + idx
                badge_class = get_badge_class(item['source'])
                channel_badge_class = get_channel_badge_class(item.get('channel', 'Programmatic'))
                pub_date_str = item['pub_date'].strftime('%B %d, %Y') if item['pub_date'] else "N/A"
                link_html = f'href="{item["link"]}" target="_blank"' if item.get('link') else ''
                
                # Render card
                card_class = "article-card article-card-selected" if item.get('selected', True) else "article-card"
                cols[idx].markdown(f"""
                <div class="{card_class}">
                    <div>
                        <span class="source-badge {badge_class}">{item['source']}</span>
                        <span class="channel-badge {channel_badge_class}">{item.get('channel', 'Programmatic')}</span>
                        <span style="font-size: 13px; color: #64748b;">📅 {pub_date_str}</span>
                        <a {link_html} class="article-title">{item['title']}</a>
                        <div class="article-snippet">{item['description'] if item['description'] else "No description available."}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Edit fields inside an expander below each card
                with cols[idx].expander("✍️ Strategic Insights & Applications", expanded=False):
                    col_sel, col_del = st.columns([3, 1])
                    with col_sel:
                        item['selected'] = st.checkbox("Include in Presentation", value=item.get('selected', True), key=f"sel_grid_{global_idx}")
                    with col_del:
                        if "custom" in item['source'].lower() or "podcast" in item['source'].lower():
                            if st.button("🗑️ Delete", key=f"del_grid_{global_idx}", use_container_width=True):
                                st.session_state.custom_items.remove(item)
                                save_agenda_state(st.session_state.articles, st.session_state.custom_items)
                                st.rerun()
                                
                    # Channel override selectbox
                    channel_options = ["Programmatic", "Brand Media", "Integrated Media"]
                    current_channel = item.get('channel', 'Programmatic')
                    try:
                        channel_idx = channel_options.index(current_channel)
                    except ValueError:
                        channel_idx = 0
                    item['channel'] = st.selectbox("Channel Tag", options=channel_options, index=channel_idx, key=f"chan_grid_{global_idx}")
                                
                    st.markdown("**Quick Insight Templates:**")
                    tpl_cols = st.columns(2)
                    tpl_keys = list(INSIGHT_TEMPLATES.keys())
                    for t_idx, t_key in enumerate(tpl_keys):
                        col_to_use = tpl_cols[t_idx % 2]
                        if col_to_use.button(t_key, key=f"tpl_grid_{global_idx}_{t_idx}"):
                            item['insight'] = INSIGHT_TEMPLATES[t_key]
                            save_agenda_state(st.session_state.articles, st.session_state.custom_items)
                            st.rerun()
                            
                    item['insight'] = st.text_area(
                        "Strategic Insight / Connection to Programmatic", 
                        value=item.get('insight', ''), 
                        placeholder="Find an insight to connect this to programmatic or brand media...",
                        key=f"ins_grid_{global_idx}"
                    )
                    item['app_brand'] = st.text_area(
                        "Application for Brand Team", 
                        value=item.get('app_brand', ''), 
                        placeholder="How the brand/client team can leverage this opportunity...",
                        key=f"app_b_grid_{global_idx}"
                    )
                    item['app_agency'] = st.text_area(
                        "Application for Agency Team", 
                        value=item.get('app_agency', ''), 
                        placeholder="How the agency/media team will execute, test, or monitor this...",
                        key=f"app_a_grid_{global_idx}"
                    )
                    if st.button("💾 Save Edits", key=f"save_grid_{global_idx}"):
                        save_agenda_state(st.session_state.articles, st.session_state.custom_items)
                        st.success("Saved!")

with tab2:
    # Presentation Mode
    selected_articles = [a for a in st.session_state.articles if a.get('selected', True)]
    selected_custom = [c for c in st.session_state.custom_items if c.get('selected', True)]
    all_selected = selected_custom + selected_articles
    
    st.markdown(f"""
    <div class="hero-section" style="padding: 30px; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0; font-size: 30px;">Programmatic & CTV News Agenda</h1>
        <p style="color: #94a3b8; margin: 10px 0 0 0; font-size: 16px;">
            📅 <b>Date:</b> {datetime.now().strftime('%B %d, %Y')} | Curated Strategic Updates
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 **Presentation Tip:** Share this tab on your screen during client calls. These strategic updates are perfect to present immediately after performance updates.")
    
    if not all_selected:
        st.warning("No items selected for the presentation. Go to the 'Curated Newsroom' tab and select some items!")
    else:
        for i, art in enumerate(all_selected, 1):
            badge_class = get_badge_class(art['source'])
            channel_badge_class = get_channel_badge_class(art.get('channel', 'Programmatic'))
            pub_date_str = art['pub_date'].strftime('%B %d, %Y') if art['pub_date'] else "N/A"
            
            st.markdown(f"""
            <div style="background-color: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; border-top: 4px solid #4f46e5; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                <span class="source-badge {badge_class}">{art['source']}</span>
                <span class="channel-badge {channel_badge_class}">{art.get('channel', 'Programmatic')}</span>
                <span style="font-size: 13px; color: #64748b;">📅 {pub_date_str}</span>
                <h2 style="color: #0f172a; margin-top: 10px; margin-bottom: 15px; font-size: 24px;">{i}. {art['title']}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Display Insight and Applications side-by-side or in clean blocks
            if art.get('insight'):
                st.markdown(f"""
                <div class="insight-box">
                    <div class="insight-title">💡 Strategic Insight / Connection to Programmatic</div>
                    <div style="color: #d46b08; font-size: 15px; line-height: 1.6;">{art['insight']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            col_b, col_a = st.columns(2)
            with col_b:
                if art.get('app_brand'):
                    st.markdown(f"""
                    <div class="app-box">
                        <div class="app-title">🏢 Application for Brand Team</div>
                        <div style="color: #389e0d; font-size: 15px; line-height: 1.6;">{art['app_brand']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.caption("No brand application specified.")
            with col_a:
                if art.get('app_agency'):
                    st.markdown(f"""
                    <div class="app-box" style="background-color: #f8fafc; border-color: #cbd5e1;">
                        <div class="app-title" style="color: #475569;">🛠️ Application for Agency Team</div>
                        <div style="color: #334155; font-size: 15px; line-height: 1.6;">{art['app_agency']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.caption("No agency application specified.")
            st.markdown("<br><hr style='border-color: #e2e8f0;'><br>", unsafe_allow_html=True)

with tab3:
    st.subheader("Export and Share the Curated Agenda")
    st.markdown("Download the curated agenda in Markdown or CSV format, or save the current state to reload it later.")
    
    selected_articles = [a for a in st.session_state.articles if a.get('selected', True)]
    selected_custom = [c for c in st.session_state.custom_items if c.get('selected', True)]
    all_selected = selected_custom + selected_articles
    
    if not all_selected:
        st.warning("No items selected. Go to the 'Curated Newsroom' tab and select some items to export!")
    else:
        # Generate Markdown text dynamically
        md_text = f"# Programmatic & CTV News Agenda\n"
        md_text += f"**Date:** {datetime.now().strftime('%B %d, %Y')} | **Timeframe:** Last Week\n\n"
        md_text += "## Summary Table\n\n"
        md_text += "| Date | Source | Title | Link |\n"
        md_text += "| --- | --- | --- | --- |\n"
        for art in all_selected:
            pub_date_formatted = art['pub_date'].strftime('%Y-%m-%d') if art['pub_date'] else "N/A"
            clean_title = art['title'].replace('|', '\\|')
            link_str = f"[Link]({art['link']})" if art['link'] else "N/A"
            md_text += f"| {pub_date_formatted} | {art['source']} | {clean_title} | {link_str} |\n"
        md_text += "\n## Strategic Insights & Applications\n\n"
        for i, art in enumerate(all_selected, 1):
            pub_date_formatted = art['pub_date'].strftime('%B %d, %Y') if art['pub_date'] else "N/A"
            md_text += f"### {i}. {art['title']}\n"
            md_text += f"- **Source:** {art['source']} | **Published:** {pub_date_formatted}\n"
            if art['link']:
                md_text += f"- **URL:** {art['link']}\n"
            if art['description']:
                md_text += f"- **Snippet:** {art['description']}\n"
            if art.get('insight'):
                md_text += f"- **Strategic Insight:** {art['insight']}\n"
            if art.get('app_brand'):
                md_text += f"- **Application for Brand Team:** {art['app_brand']}\n"
            if art.get('app_agency'):
                md_text += f"- **Application for Agency Team:** {art['app_agency']}\n"
            md_text += "\n---\n\n"

        st.text_area("Markdown Content", value=md_text, height=400)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Markdown Report",
                data=md_text,
                file_name=f"programmatic_news_report_{datetime.now().strftime('%Y-%m-%d')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col2:
            # Generate CSV string
            import io
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(['Date', 'Source', 'Title', 'URL', 'Snippet', 'Insight', 'Application Brand', 'Application Agency'])
            for art in all_selected:
                pub_date_formatted = art['pub_date'].strftime('%Y-%m-%d') if art['pub_date'] else "N/A"
                writer.writerow([
                    pub_date_formatted, 
                    art['source'], 
                    art['title'], 
                    art['link'], 
                    art['description'],
                    art.get('insight', ''),
                    art.get('app_brand', ''),
                    art.get('app_agency', '')
                ])
            
            st.download_button(
                label="📥 Download CSV Report",
                data=csv_buffer.getvalue(),
                file_name=f"programmatic_news_report_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
