---
name: zoom-get-meeting-summary
description: Fetches the AI Companion meeting summary for a specific meeting instance.
parameters:
  meeting-uuid:
    type: string
    description: The unique occurrence UUID or ID of the meeting instance.
    required: true
---

# zoom-get-meeting-summary

Fetches the AI Companion meeting summary for a specific meeting instance.

### Prerequisites

- `ZOOM_CLIENT_ID`
- `ZOOM_REFRESH_TOKEN`

### Command to Execute

```bash
python3 .agents/skills/zoom-get-meeting-summary/scripts/get_meeting_summary.py --meeting-uuid "{meeting-uuid}"
```
