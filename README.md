# whoop-cli

CLI tool to pull Whoop health data from the terminal. Works for humans and as a data source for Claude Code/LLMs.

## Install

```bash
pip install -e .
```

## Setup

1. Register an app at [developer.whoop.com](https://developer.whoop.com)
2. Set redirect URI to `http://localhost:8910/callback`
3. Copy your credentials:

```bash
cp .env.example .env
# Edit .env with your WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET
```

4. Authenticate:

```bash
whoop auth login
```

## Usage

```bash
# Daily queries
whoop sleep today
whoop recovery today
whoop strain today
whoop summary today
whoop summary week

# Date ranges
whoop sleep --from 2026-03-01 --to 2026-03-15
whoop recovery --from 2026-03-01

# Profile
whoop profile

# Export
whoop export --from 2026-01-01 --format json > data.json
whoop export --from 2026-01-01 --format csv > data.csv

# Output formats: json (default for pipes), md (default for TTY), csv
whoop recovery today --format md
whoop sleep week --format csv
```

## Environment Variables

- `WHOOP_CLIENT_ID` — OAuth client ID
- `WHOOP_CLIENT_SECRET` — OAuth client secret
- `WHOOP_ACCESS_TOKEN` — Skip OAuth, use this token directly (CI/headless)
