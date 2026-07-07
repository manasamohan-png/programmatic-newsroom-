---
name: cross-referencer
description: Cross-references a YouTube channel target list with a weekly YouTube channel block list and generates a cleaned block list that does not contain any of the target channels.
parameters:
  target-list:
    type: string
    description: Path to the channel target list Excel file (.xlsx)
    required: true
  block-list:
    type: string
    description: Path to the YT channel block list Excel file (.xlsx)
    required: true
  output-path:
    type: string
    description: Path to save the cleaned block list Excel file (.xlsx)
    required: false
---

# cross-referencer

This skill cross-references a YouTube channel target list with a weekly YouTube channel block list and generates a cleaned block list that does not contain any of the target channels.

### Prerequisites

No external API credentials or environment variables are required. This skill runs entirely locally using Python and pandas.

### Command to Execute

```bash
python3 .agents/skills/cross-referencer/scripts/cross_reference.py --target-list "{target-list}" --block-list "{block-list}" --output-path "{output-path}"
```
