# ZhihuSpider

> **Enhanced edition** of [lemoabc/ZhihuSpider](https://github.com/lemoabc/ZhihuSpider)  
> Adds cross-platform compatibility, incremental crawling, unique filenames, and **multi-user support**.

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-blue?logo=apple&logoColor=white)](https://github.com)

## Overview

ZhihuSpider is a lightweight crawler for [Zhihu](https://www.zhihu.com) (知乎) content. It supports:

- **Two engines** — `nav_crawler.py` (v4, browser-navigation, recommended) and `run.py` (v3 HTTP engine, see status below)
- **Multi-user** — specify any Zhihu username (`--user <USERNAME>`)
- **Incremental crawling** — skips already-crawled items via `.index_*.json` files
- **Unique filenames** — `{title}_{id}.md` avoids collision between items with similar titles
- **YAML frontmatter** — Chinese field names (标题/作者/日期/链接/类型/标签/摘要)
- **Externalized configuration** — all personal paths stored in `config.local.json` (gitignored)

> ⚠️ **2026-09 anti-bot status**: Zhihu now enforces `x-zse-93/96` signing on XHR-type
> requests — plain `requests` and in-page `fetch` both get `403 code 40362`.
> **Browser top-level navigation** to the API URL is unsigned and returns pure JSON.
> The v3 HTTP engine (`run.py`/`crawler.py`) is expected to be blocked; use the v4
> engine below.

## v4 Engine (recommended): browser-navigation crawler

```bash
pip install -r requirements.txt   # includes playwright

# Answers (requires a Chromium-based browser logged into Zhihu on this machine)
python nav_crawler.py --user <URL_TOKEN> --output ./backup/answers
# Articles
python nav_crawler.py --user <URL_TOKEN> --kind article --output ./backup/articles
# Options: --max N --pages N --delay-min/--delay-max --browser auto|edge|chrome
#          --headful --keep-profile --cookie-file cookies.json
```

How it works: auto-detects installed Edge/Chrome → takes an atomic `sqlite3.backup()`
snapshot of the cookie DB and deletes all non-Zhihu rows in place (passwords, history,
other sites' cookies never leave the directory) → launches a throwaway temp profile
(deleted on exit) → warms up zhihu.com (first-navigation-to-API is flagged as a
third-party request) → navigates the API URL page by page.

Key implementation notes (all hard-won):
- Playwright's default `--use-mock-keychain` must be dropped via `ignore_default_args`,
  otherwise copied encrypted cookies silently fail to decrypt (empty jar).
- Cookie DB layout differs by browser (`Default/Cookies` vs `Default/Network/Cookies`) —
  the copy must land at the same relative path the browser reads.
- Legacy v2.x indexes (`.index_回答.json`) are auto-inherited to avoid re-crawling.
- Cookie encryption keys are bound to *machine + OS user + browser*; on a new machine,
  log into Zhihu once in any Chromium-based browser, or use `--cookie-file`.

## Quick Start (v3 HTTP engine — expected blocked since 2026-09)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure (see config.json for all keys)
cp config.json config.local.json
# Edit config.local.json with your cookie file path, output dir, etc.

# 3. Run — specify the target Zhihu username
python run.py --user <USERNAME>               # crawl all content (answers + articles)
python run.py --user <USERNAME> --only-answers    # answers only
python run.py --user <USERNAME> --only-articles   # articles only
python run.py --user <USERNAME> --cookie ./cookies.json
python run.py --user <USERNAME> --output ./my_backup
python run.py --user <USERNAME> --no-cookie-inject    # skip cookie injection
```

## Configuration

Copy `config.json` to `config.local.json` and edit:

| Key | Description |
|-----|-------------|
| `username` | Default Zhihu username (can override via `--user`) |
| `cookie_file` | Path to Edge/Chrome-exported cookies JSON file |
| `output_dir` | Default directory to save `.md` files |
| `cdp_port` | CDP port for cookie injection (default: 9222) |
| `edge_profile_dir` | Edge user-data directory (for cookie injection) |
| `request_delay` | Delay between API requests (seconds) |
| `retry_max` | Max retry attempts for failed requests |
| `retry_delay` | Delay between retries (seconds) |

> `config.local.json` is **gitignored** — it never commits to the repo.
> `cookie_file` contains session data — **never commit it**.

## Architecture

```
crawler.py          → Core crawling engine (HTTP requests)
cookie_injector.py  → Cookie injection/management via CDP WebSocket
browser_finder.py   → Auto-detects Edge/Chrome binary path
config.json         → Template config (committed)
config.local.json   → User config (gitignored)
run.py              → CLI entry point (main interface)
crawl_all.sh        → All-in-one script (launch Edge + crawl)
scripts/edge_*.sh   → Edge management scripts for persistent profiles
```

Each crawl fetches paginated API responses:
- `api/v4/members/{uid}/answers`
- `api/v4/members/{uid}/articles`

Items are filtered against `.index_answer.json` / `.index_article.json` for incremental crawling.

Each output file contains YAML frontmatter + Markdown content.

## Usage Details

### Getting Cookies

```bash
# Export cookies from Edge (runs in headless mode)
python cookie_injector.py --export-cookies cookies.json
```

Make sure you're logged into zhihu.com in your Edge/Chrome browser first.

### Running Crawls

```bash
# Full crawl (answers + articles)
python run.py --user exampleuser

# With custom cookie file and output path
python run.py -u exampleuser -c /path/to/cookies.json -o ./my_backup

# Articles only, skip cookie injection
python run.py -u exampleuser --only-articles --no-cookie-inject
```

### Shell Script Alternative

For macOS users that need Edge to stay alive:

```bash
./crawl_all.sh
```

Or run Edge as a persistent background process:

```bash
./scripts/edge_launcher.sh start
# ... run crawler ...
./scripts/edge_launcher.sh stop
```

## Rate Limiting & Safety

- Default delay: 2–5 seconds between pages (configurable in `config.json`)
- Jitter added: ±0.5–1.0 second randomization
- Max retry: 3 attempts per page with exponential backoff
- Capped page fetches: add `--pages 50` to limit total pages

## Known Issues

- Cookie expiry: Zhihu cookies typically expire in 7–30 days. Export new ones when crawls fail with 401/403.
- Rate limits: Some users may get rate-limited even with delays. Use smaller page limits if needed.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Upstream

Enhanced from [lemoabc/ZhihuSpider](https://github.com/lemoabc/ZhihuSpider) by lemoabc.
