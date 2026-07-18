# ZhihuSpider

> **Enhanced edition** of [lemoabc/ZhihuSpider](https://github.com/lemoabc/ZhihuSpider)  
> Adds cross-platform compatibility, incremental crawling, and unique filenames.

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-blue?logo=apple&logoColor=white)](https://github.com)

## Overview

ZhihuSpider is a lightweight crawler for [Zhihu](https://www.zhihu.com) (知乎) content. It supports:

- **Incremental crawling** — skips already-crawled items via `.index_*.json` files
- **Unique filenames** — `{title}_{id}.md` avoids collision between items with similar titles
- **YAML frontmatter** — Chinese field names (标题/作者/日期/链接/类型/标签/摘要)
- **Clean HTTP implementation** — uses `requests` for API crawling, no browser overhead
- **Externalized configuration** — all personal paths stored in `config.local.json` (gitignored)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure (see config.json for all keys)
cp config.json config.local.json
# Edit config.local.json with your username, cookie file, output dir

# 3. Run
python crawler.py --help
python crawler.py -k answer          # crawl answers
python crawler.py -k article         # crawl articles
python crawler.py -k answer -o ./my_backup --max 100  # limit to 100 items
```

## Configuration

| Key | Description |
|-----|-------------|
| `username` | Zhihu username |
| `cookie_file` | Path to Edge-exported cookies JSON |
| `output_dir` | Directory to save `.md` files |
| `cdp_port` | CDP port for cookie injection (default: 9222) |
| `edge_profile_dir` | Edge user-data directory (for cookie injection) |

> `config.local.json` is **gitignored** — it never commits to the repo.

## Architecture

```
crawler.py         → Core crawling engine (HTTP requests)
cookie_injector.py → Cookie injection/management
browser_finder.py  → Auto-detects Edge/Chrome binary path
config.json        → Template config (committed)
config.local.json  → User config (gitignored)
```

Each crawl fetches paginated API responses:
- `api/v4/members/{uid}/answers`
- `api/v4/members/{uid}/articles`

Items are filtered against `.index_answer.json` / `.index_article.json` for incremental crawling.

Each output file contains YAML frontmatter + Markdown content.

## Notes

- Cookie JSON files contain session data — **never commit them**
- Rate limiting: 2–5s between pages
- For cookie injection, Edge must be running with CDP enabled (see `cookie_injector.py --help`)

## License

MIT License — see [LICENSE](LICENSE) for details.

## Upstream

Enhanced from [lemoabc/ZhihuSpider](https://github.com/lemoabc/ZhihuSpider) by lemoabc.
