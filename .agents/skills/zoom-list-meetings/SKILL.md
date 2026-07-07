---
name: zoom-list-meetings
description: Lists Zoom meetings (both scheduled occurrences and past instances) for a specified date range.
parameters:
  start-date:
    type: string
    description: The start date to filter meetings (YYYY-MM-DD). Defaults to 30 days ago.
    required: false
  end-date:
    type: string
    description: The end date to filter meetings (YYYY-MM-DD). Defaults to today.
    required: false
  search:
    type: string
    description: Search term to filter meetings by topic or agenda.
    required: false
---

# zoom-list-meetings

Lists Zoom meetings (both scheduled occurrences and past instances) for a specified date range, with optional keyword searching.

### Prerequisites

- `ZOOM_CLIENT_ID`
- `ZOOM_REFRESH_TOKEN`

### Command to Execute

```bash
python3 .agents/skills/zoom-list-meetings/scripts/list_meetings.py --start-date "{start-date}" --end-date "{end-date}" --search "{search}"
```
