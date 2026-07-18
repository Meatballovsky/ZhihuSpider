"""
================================================================================
# Agent Project Metadata
# Project ID: zhihubf
# Registry:      ~/agent_projects/projects.json
# Manifest:      ~/agent_projects/zhihubf/metadata.json
# Version:      1.0.3
# Status:      Stable
# Owner:       User
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
Zhihu Backup Crawler - 
==================================

This tool crawls all answers and articles from the Zhihu user 
(Username: "") and saves them as Markdown files locally.

Key features:
    - Incremental crawl (skips already-crawled items via .index_*.json)
    - Unique filenames: {title}_{answer_id}.md
    - Cross-platform (macOS, Linux, Windows)
    - YAML frontmatter in each Markdown file

Usage:
    source venv/bin/activate
    python run.py [options]

Options:
    --help, -h            Show this help message
    --output DIR          Output directory (default: ~/Desktop/zhihubf/)
    --cookie FILE         Cookie JSON file path
    --only-answers        Only crawl answers section
    --only-articles       Only crawl articles section
    --browser PATH        Path to Chrome/Edge binary (auto-detect if omitted)
    --cdp-port PORT       CDP port for cookie injection (default: 9222)
    --no-cookie-inject    Skip cookie injection step

Examples:
    python run.py
    python run.py --output ./my_backup --cookie ./cookies.json
    python run.py --only-articles
    python run.py --no-cookie-inject  # cookies already in browser

Notes:
    - Ensure Edge is running on the CDP port before crawling.
    - First crawl may take longer as it downloads all pages.
    - Subsequent crawls only fetch new content (incremental).
"""
    print(help_text)


def main():
    parser = argparse.ArgumentParser(
        description="Zhihu Backup Crawler - ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=str,
        default=ZHIHU_OUTPUT,
        help="Output directory (default: " + ZHIHU_OUTPUT + ")",
    )
    parser.add_argument(
        "--cookie",
        type=str,
        default=COOKIE_FILE,
        help="Cookie JSON file path (default: " + COOKIE_FILE + ")",
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
        help="CDP port (default: 9222, from agent_edge_launcher)",
    )
    parser.add_argument(
        "--no-cookie-inject",
        action="store_true",
        help="Skip cookie injection step (cookies already in browser)",
    )

    args = parser.parse_args()

    # Handle help-only mode
    if not args.cookie and not args.browser and args.only_answers and args.only_articles:
        print_help()
        return 0

    # Step 1: Cookie injection (unless skipped)
    # Cookie injection is now handled inside crawler.py via WebPage.cookies API.
    # If you want to inject manually first, use:
    #   python cookie_injector.py

    # Step 2: Import crawler modules
    from crawler import crawl_content
    from browser_finder import find_browser

    # Find browser binary
    browser_path = args.browser or find_browser()
    
    # Step 3: Crawl
    try:
        if args.only_answers:
            from crawler import USER_ID
            count = crawl_content(kind="answer", output_dir=args.output, cookie_file=args.cookie)
            print(f"\nAnswer crawl complete: {count} new answers crawled")
        elif args.only_articles:
            count = crawl_content(kind="article", output_dir=args.output, cookie_file=args.cookie)
            print(f"\nArticle crawl complete: {count} new articles crawled")
        else:
            print("\n=== Crawling answers...")
            ans = crawl_content(kind="answer", output_dir=args.output, cookie_file=args.cookie)
            print(f"=== Crawling articles...")
            art = crawl_content(kind="article", output_dir=args.output, cookie_file=args.cookie)
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
