---
name: snapchat-list-ad-accounts
description: Lists all available Snapchat Ad Accounts and their IDs for the current active account.
---

# list_snapchat_ad_accounts

This skill fetches and lists all Snapchat Ad Accounts inside all Organizations accessible to the currently active `.env` configuration. It properly generates a fresh access token from the authorized `SNAPCHAT_REFRESH_TOKEN` to ensure compliance with the safety directives.

**IMPORTANT**: ALWAYS run the `which_customer` skill first if you aren't sure which customer environment is active.

### Command to Execute
```bash
python3 .agents/skills/snapchat-list-ad-accounts/scripts/list_accounts.py
```

### Output
The command returns a formatted table with:
- `Account Name`
- `Account ID`

## Notes

- **Snapchat API Authentication**: For any Snapchat-specific skills, do NOT rely on a stored `SNAPCHAT_ACCESS_TOKEN`. Instead, you must read the `SNAPCHAT_REFRESH_TOKEN` from the `.env` file and exchange it for a new short-lived access token at the beginning of every API call or script execution.