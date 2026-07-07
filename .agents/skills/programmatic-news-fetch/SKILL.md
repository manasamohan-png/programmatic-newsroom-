---
name: programmatic-news-fetch
description: Fetches, deduplicates, and compiles the latest programmatic, brand, and integrated media news articles from Google News, Digiday, AdExchanger, eMarketer, WSJ (CMO Today), NYT, NPR, and top ad tech podcasts.
parameters:
  days:
    type: integer
    description: Number of days of news to fetch (default is 7).
    required: false
  output-dir:
    type: string
    description: Directory to save the generated Markdown and CSV reports (default is current directory).
    required: false
  slack-channel:
    type: string
    description: Optional Slack channel ID, channel name, or user name/email/ID to send a summary of the report to (e.g. #general, john@company.com, U12345678).
    required: false
  schedule:
    type: boolean
    description: Schedule this script to run automatically via macOS launchd.
    required: false
  sources:
    type: string
    description: Comma-separated list of sources to fetch (options: deals, digiday, adexchanger, emarketer, wsj, nyt, npr, podcasts; default is deals,digiday,adexchanger,emarketer,wsj,nyt,npr,podcasts).
    required: false
  interval:
    type: integer
    description: Interval in seconds for the scheduled task (default is 604800 / 7 days).
    required: false
---

# programmatic-news-fetch

This skill fetches, deduplicates, and compiles the latest programmatic, brand, and integrated media news articles from Google News, Digiday, AdExchanger, eMarketer, Wall Street Journal (CMO Today), New York Times, NPR, and top ad tech podcasts (AdExchanger Talks, Marketecture). It automatically classifies articles into channels (Programmatic, Brand Media, Integrated Media), generates Markdown and CSV reports, and can send a summary directly to a Slack channel or individual user. It also supports scheduling itself to run automatically on macOS every Monday at 8:00 AM.

### Prerequisites

- Optional: `SLACK_CLIENT_ID` and `SLACK_REFRESH_TOKEN` in your `.env` file if you want to send notifications to Slack.

### Command to Execute

```bash
python3 .agents/skills/programmatic-news-fetch/scripts/fetch_news.py --days {days} --output-dir "{output-dir}" --slack-channel "{slack-channel}" {schedule} --sources "{sources}" --interval {interval}
```

### Streamlit Web Application

A beautiful, interactive Streamlit web application is available to view, search, filter, and manually trigger news fetches.

To run the web application:
```bash
python3 -m streamlit run app.py
```