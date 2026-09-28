"""
================================================================================
# 🤖 AGENT PROJECT METADATA
# Project ID: zhihubf
# Registry:     ~/agent_projects/projects.json
# Manifest:     ~/agent_projects/zhihubf/metadata.json
# Version:         4.0.0
# Status:      Stable
# Owner:       Agent/User
================================================================================

Zhihu Backup Crawler - Entry Point

Prerequisite (REQUIRED - see README.md):
    1. Start Edge: see README.md for Edge setup
    2. Inject cookies:   python cookie_injector.py

Configuration (config.json):
    Copy config.json to config.local.json and edit it with your personal paths.
    config.local.json is automatically loaded (and is ignored by git).

Usage:
    source venv/bin/activate
    python run.py --help
    python run.py                               # crawl with config defaults
    python run.py --output ~/Desktop/my_backup   # custom output dir
    python run.py --cookie /path/cookies.json   # use different cookie file
    python run.py --only-articles               # only articles
    python run.py --no-cookie-inject            # skip cookie injection
"""

from __future__ import annotations

import argparse
import json
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load config: prefer config.local.json (user-specific, gitignored), fallback to config.json
_CONFIG_FILE = os.path.join(PROJECT_DIR, "config.local.json")
if os.path.isfile(_CONFIG_FILE):
    with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
        _CONFIG = json.load(f)
else:
    _CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")
    if os.path.isfile(_CONFIG_FILE):
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            _CONFIG = json.load(f)
    else:
        _CONFIG = {}

ZHIHU_OUTPUT = _CONFIG.get("output_dir", os.path.join(os.path.expanduser("~"), "Desktop", "zhihubf", "zhihu"))
COOKIE_FILE = _CONFIG.get("cookie_file", os.path.join(PROJECT_DIR, "cookies.json"))
CDP_PORT = _CONFIG.get("cdp_port", 9222)
USERNAME = _CONFIG.get("username", "")
EDGE_PROFILE_DIR = _CONFIG.get("edge_profile_dir", os.path.join(PROJECT_DIR, "edge_agent_profile"))


def print_help():
    help_text = """
Zhihu Crawler - Universal multi-user crawler
==============================================

This tool crawls answers and articles from ANY Zhihu user
and saves them as Markdown files locally.

Key features:
     - Incremental crawl (skips already-crawled items via .index_*.json)
     - Unique filenames: {title}_{answer_id}.md
     - Cross-platform (macOS, Linux, Windows)
     - YAML frontmatter in each Markdown file
     - Multi-user: specify any Zhihu username

Usage:
    source venv/bin/activate
    python run.py --user <USERNAME>            # crawl all content
    python run.py --user <USERNAME> --help     Show help
    python run.py --user <USERNAME> --only-answers     # answers only
    python run.py --user <USERNAME> --only-articles    # articles only
    python run.py --user <USERNAME> --output ./my_backup
    python run.py --user <USERNAME> --cookie ./cookies.json
    python run.py --user <USERNAME> --no-cookie-inject   # cookies already in browser

Examples:
    python run.py --user exampleuser
    python run.py --user exampleuser --only-articles
    python run.py --user exampleuser --output ./backup --max 100
    python run.py --user exampleuser --no-cookie-inject

Notes:
     - Cookies must be exported from Edge/Chrome first (see cookie_injector.py)
     - First crawl may take longer as it downloads all pages
     - Subsequent crawls only fetch new content (incremental)
"""
    print(help_text)


def main():
    parser = argparse.ArgumentParser(
        description="Zhihu Crawler - Universal multi-user crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
     )
    parser.add_argument(
         "--user", "-u",
         type=str,
         required=True,
         help="Zhihu username (e.g., exampleuser)",
     )
    parser.add_argument(
         "--output", "-o",
         type=str,
         default=None,
         help="Output directory (default: ~/Desktop/zhihubf/<username>)",
     )
    parser.add_argument(
         "--cookie", "-c",
         type=str,
         default=None,
         help="Cookie JSON file path",
     )
    parser.add_argument(
         "--only-answers",
         action="store_true",
         help="Only crawl answers section",
     )
    parser.add_argument(
         "--only-articles",
         action="store_true",
         help="Only crawl articles section",
     )
    parser.add_argument(
         "--browser",
         type=str,
         default=None,
         help="Path to Chrome/Edge binary (auto-detect if omitted)",
     )
    parser.add_argument(
         "--cdp-port",
         type=int,
         default=CDP_PORT,
         help=f"CDP port (default: {CDP_PORT})",
     )
    parser.add_argument(
         "--no-cookie-inject",
         action="store_true",
         help="Skip cookie injection step (cookies already in browser)",
     )

    args = parser.parse_args()

     # Determine output directory
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            "zhihubf",
            args.user
        )

     # Cookie injection (unless skipped or cookie file already provided)
    if not args.no_cookie_inject and args.cookie:
        print(f"  Injecting cookies from {args.cookie}...")
        from cookie_injector import inject_cookies
        injected = inject_cookies(args.cookie, args.cdp_port)
        print(f"  Injected {len(injected)} cookies")
    elif not args.no_cookie_inject:
        print(f"  No cookie file specified. Skipping cookie injection.")
        print(f"  Or use: --cookie path/to/cookies.json")

     # Step 2: Import crawler module
    from crawler import crawl_content

     # Step 3: Crawl
    try:
        if args.only_answers:
            count = crawl_content(
                kind="answer", user_id=args.user,
                output_dir=output_dir, cookie_file=args.cookie or "",
            )
            print(f"\nAnswer crawl complete: {count} new answers crawled")
        elif args.only_articles:
            count = crawl_content(
                kind="article", user_id=args.user,
                output_dir=output_dir, cookie_file=args.cookie or "",
            )
            print(f"\nArticle crawl complete: {count} new articles crawled")
        else:
            print(f"\n=== Crawling answers for user: {args.user} ===")
            ans = crawl_content(
                kind="answer", user_id=args.user,
                output_dir=output_dir, cookie_file=args.cookie or "",
            )
            print(f"\n=== Crawling articles for user: {args.user} ===")
            art = crawl_content(
                kind="article", user_id=args.user,
                output_dir=output_dir, cookie_file=args.cookie or "",
            )
            print(f"\nCrawl complete: {ans} answers, {art} articles")
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError during crawl: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
