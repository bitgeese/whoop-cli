# whoop-cli — Build Prompt for Claude Code

> A Python CLI tool to pull Whoop health data from the terminal. Designed to be used by humans AND by Claude Code/LLMs as a data source.

## What to Build

A lightweight CLI called `whoop` (package name: `whoop-cli`) that wraps the Whoop API v2 and outputs structured data (JSON or markdown) to stdout. Think of it as `gh` (GitHub CLI) but for your body.

## Commands

### Daily Queries
```bash
whoop sleep today              # last night's sleep summary
whoop sleep yesterday
whoop recovery today           # recovery score, HRV, resting HR
whoop strain today             # day strain + workouts
whoop summary today            # combined: sleep + recovery + strain in one view
whoop summary week             # last 7 days overview
```

### Historical / Range Queries
```bash
whoop sleep --from 2026-03-01 --to 2026-03-15
whoop recovery --from 2026-03-01 --to 2026-03-15
whoop workouts --from 2026-03-01 --to 2026-03-15
whoop cycles --from 2026-03-01 --to 2026-03-15
```

### Profile & Setup
```bash
whoop auth login               # OAuth 2.0 flow — opens browser, stores token
whoop auth status              # show current auth state
whoop auth logout              # revoke token
whoop profile                  # name, email, body measurements
```

### Export
```bash
whoop export --from 2026-01-01 --format json > whoop-dump.json
whoop export --from 2026-01-01 --format csv > whoop-dump.csv
whoop export --from 2026-01-01 --format md > whoop-dump.md
```

## Output Formats

Every command supports `--format` flag:
- `json` (default) — structured, machine-readable, perfect for Claude Code
- `md` — human-readable markdown table/summary
- `csv` — flat export for spreadsheets

Default to `json` so LLMs can parse it easily. Detect if stdout is a TTY and switch to `md` for human use (like how `gh` does it).

## Tech Stack

- **Python 3.10+**
- **Typer** — CLI framework (auto-generates help, clean DX)
- **httpx** — async HTTP client for API calls
- **Pydantic v2** — response models, validation
- **keyring** — secure token storage (OS keychain)
- **rich** — pretty terminal output for markdown mode

Do NOT use the `whoopy` library — build the API client from scratch for full control and fewer dependencies. The API is simple enough.

## Whoop API v2 Reference

- **Base URL**: `https://api.prod.whoop.com/developer/v1`
- **Auth**: OAuth 2.0 (Authorization Code flow)
  - Register app at https://developer.whoop.com
  - Scopes: `read:profile`, `read:body_measurement`, `read:cycles`, `read:recovery`, `read:sleep`, `read:workout`
  - Token refresh: use refresh_token grant
- **Pagination**: all collection endpoints return `next_token`, pass it back to get next page. Max 25 per page.
- **Date filtering**: `start` and `end` query params in ISO 8601 format

### Endpoints
| Endpoint | Description |
|---|---|
| `GET /v1/user/profile/basic` | User profile (name, email) |
| `GET /v1/user/measurement/body` | Body measurements (height, weight, max HR) |
| `GET /v1/cycle` | All physiological cycles (paginated, date-filterable) |
| `GET /v1/cycle/{id}` | Single cycle by ID |
| `GET /v1/recovery` | All recovery records (paginated, date-filterable) |
| `GET /v1/recovery/cycle/{cycleId}` | Recovery for specific cycle |
| `GET /v1/sleep` | All sleep records (paginated, date-filterable) |
| `GET /v1/sleep/{id}` | Single sleep by ID |
| `GET /v1/workout` | All workouts (paginated, date-filterable) |
| `GET /v1/workout/{id}` | Single workout by ID |

### Key Data Fields

**Recovery**: `score.recovery_score`, `score.hrv_rmssd_milli` (HRV in ms), `score.resting_heart_rate`, `score.spo2_percentage`, `score.skin_temp_celsius`

**Sleep**: `score.stage_summary` (wake/light/slow_wave/rem durations), `score.sleep_performance_percentage`, `score.sleep_efficiency_percentage`, `score.respiratory_rate`

**Cycle**: `score.strain`, `score.kilojoule`, `score.average_heart_rate`, `score.max_heart_rate`

**Workout**: `score.strain`, `score.average_heart_rate`, `score.max_heart_rate`, `score.kilojoule`, `score.distance_meter`, `sport_id`

## Project Structure

```
whoop-cli/
├── README.md
├── pyproject.toml              # use hatchling or setuptools
├── src/
│   └── whoop_cli/
│       ├── __init__.py
│       ├── cli.py              # Typer app, all commands
│       ├── client.py           # httpx-based API client
│       ├── auth.py             # OAuth flow + token management
│       ├── models.py           # Pydantic models for API responses
│       ├── formatters.py       # json/md/csv output formatters
│       └── config.py           # settings, paths, defaults
├── tests/
│   ├── test_client.py
│   ├── test_formatters.py
│   └── test_cli.py
└── .env.example                # WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET
```

## Auth Flow

1. User runs `whoop auth login`
2. CLI opens browser to Whoop OAuth URL with redirect to `http://localhost:8910/callback`
3. Tiny local HTTP server catches the callback, extracts auth code
4. Exchange code for access_token + refresh_token
5. Store tokens in OS keychain via `keyring`
6. On subsequent calls, auto-refresh if token expired

For CI/headless use, support `WHOOP_ACCESS_TOKEN` env var override.

## Pagination Helper

All collection endpoints need auto-pagination. Build a generic async generator:

```python
async def paginate(endpoint: str, params: dict) -> AsyncGenerator[dict, None]:
    while True:
        response = await client.get(endpoint, params=params)
        data = response.json()
        for record in data["records"]:
            yield record
        if not data.get("next_token"):
            break
        params["nextToken"] = data["next_token"]
```

## Publishing

- Package name on PyPI: `whoop-cli`
- Entry point: `whoop` command
- Include a `LICENSE` (MIT)
- README with install instructions, usage examples, screenshots

## Quality

- Type hints everywhere
- Tests with pytest + httpx mock
- Pre-commit: ruff for linting/formatting
- GitHub Actions CI

## What NOT to Build (Yet)

- No webhooks / real-time streaming
- No data visualization (that's a separate tool)
- No database storage (just stdout + optional file export)
- No continuous HR (not available via API anyway)

## Existing Reference Implementations

Look at these for inspiration:
- `nissand/whoop-mcp-server-claude` — TypeScript MCP server, 18+ endpoints, full OAuth
- `hedgertronic/whoop` — Python, good data extraction patterns
- `JedPattersonn/whoop-mcp` — another MCP server implementation
- `zachgodsell93/Get-My-Whoop` — simple Python extraction

## Bonus: Claude Code Skill

After the CLI is built, create a Claude Code skill at `.claude/skills/whoop/SKILL.md` that teaches Claude how to use the CLI to answer health questions like "how did I sleep this week?" or "show me my recovery trend for March".
