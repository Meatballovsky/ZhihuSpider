"""
================================================================================
# 🤖 AGENT PROJECT METADATA
# Project ID: zhihubf
# Registry:             ~/agent_projects/projects.json
# Manifest:              ~/agent_projects/zhihubf/metadata.json
# Version:                 3.2.0
# Status:          Stable
# Owner:           Agent/User
================================================================================

crawler.py - Zhihu Crawler (HTTP requests edition, v3.2).

Key changes from v2.x (DrissionPage listener edition):
    - Uses DrissionPage ONLY for initial cookie extraction
    - Uses `requests` + `Session` for all API crawling (reliable, no browser hang)
    - Keeps YAML frontmatter, incremental index, and file naming conventions
    - Adds retry, rate limiting, resumable pagination, and progress tracking
    - Generic: no hardcoded username, configurable via config file

Dependencies:
    requests >= 2.31.0      (pip install requests)
    DrissionPage >= 4.1.0     (only for cookie extraction if needed)
    beautifulsoup4 >= 4.12.0
    lxml >= 5.0

Configuration:
    - Create config.local.json (copied from config.json) with your personal paths.
    - config.local.json is gitignored.
    - All runtime config is READ from config file at import time.

Prerequisites:
    1. Create config.local.json from config.json and set your paths
    2. Login to zhihu.com in Edge or Chrome
    3. Export cookies: python cookie_injector.py --export-cookies cookies.json
    4. Run: python crawler.py --user <USERNAME>
"""
from __future__ import annotations

import json
import os
import re
import time
import random
import requests
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Callable

# ---------------------------------------------------------------------------
# Configuration - loaded from config.json or config.local.json
# ---------------------------------------------------------------------------
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.local.json")
if not os.path.isfile(_CONFIG_PATH):
    _CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
    _CONFIG = json.load(_f)
CONFIG_COOKIE_FILE = _CONFIG.get("cookie_file", "cookies.json")
CONFIG_CDP_PORT = _CONFIG.get("cdp_port", 9222)

CONTENT_CONFIGS = {
    "answer": {
        "label": "回答",
        "api_url": "https://www.zhihu.com/api/v4/members/{uid}/answers",
        "params": {
            "include": (
                "data[*].is_normal,answer_type,voteup_count,comment_count,created,"
                "content,author,voting,copyright_permission,"
                "is_sticky,content_voting,is_labeled,rating,is_author_pinned,no_basecard"
            ),
            "sort_by": "created",
        },
        "file_prefix": "回答",
        "url_base": "https://www.zhihu.com/question/{question_id}/answer/{answer_id}",
        "index_file": ".index_answer.json",
    },
    "article": {
        "label": "文章",
        "api_url": "https://www.zhihu.com/api/v4/members/{uid}/articles",
        "params": {
            "include": (
                "data[*].voteup_count,comment_count,created,"
                "like_count,is_sticky,content,author,copyright_info"
            ),
            "sort_by": "created",
        },
        "file_prefix": "文章",
        "url_base": "https://zhuanlan.zhihu.com/p/{article_id}",
        "index_file": ".index_article.json",
    },
}


# ---------------------------------------------------------------------------
# Cookie management
# ---------------------------------------------------------------------------
def load_cookies_from_json(cookie_path: str) -> dict:
    """Load cookies from the Edge-exported JSON file."""
    with open(cookie_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)
    return {c["name"]: c["value"] for c in raw_list}


def cookies_to_requests_session(cookies: dict, session=None) -> requests.Session:
    """Load cookies into a requests Session, preserving all headers."""
    if session is None:
        session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain=".zhihu.com", path="/")
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.zhihu.com/",
        "x-requested-with": "fetch",
        "origin": "https://www.zhihu.com",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    return session


# ---------------------------------------------------------------------------
# HTML to markdown conversion (same as v2.x)
# ---------------------------------------------------------------------------
def sanitize_filename(name):
    """Sanitize filename by removing illegal characters."""
    return re.sub(r'[\\/:*?"<>|\n\t]', '', name)[:80]


def html_to_md(html: str) -> str:
    """Convert HTML to markdown using BeautifulSoup."""
    if not html:
        return ""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        text = re.sub(r'<[^>]+>', ' ', html)
        return re.sub(r'\s{2,}', ' ', text).strip()

    soup = BeautifulSoup(html, "lxml")

    # Images
    for img in soup.find_all("img"):
        src = img.get("data-original") or img.get("data-actualsrc") or img.get("src", "")
        alt = img.get("alt", "")
        img.replace_with(f"![{alt}]({src})")

    # Links
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text()
        if href and text:
            a.replace_with(f"[{text}]({href})")

    # Headings
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(tag.name[1])
        tag.replace_with("#" * level + " " + tag.get_text() + "\n\n")

    # Text modifiers
    for tag in soup.find_all(["b", "strong"]):
        tag.replace_with("**" + tag.get_text() + "**")
    for tag in soup.find_all(["i", "em"]):
        tag.replace_with("*" + tag.get_text() + "*")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.replace_with(p.get_text() + "\n\n")
    for li in soup.find_all("li"):
        li.replace_with("- " + li.get_text() + "\n")
    for bq in soup.find_all("blockquote"):
        lines = bq.get_text().strip().split("\n")
        bq.replace_with("\n".join("> " + line for line in lines) + "\n\n")

    text = soup.get_text()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Item parsing helpers
# ---------------------------------------------------------------------------
def _parse_answer_item(item: dict, uid: str) -> Optional[dict]:
    """Parse a single answer API response into a unified item dict."""
    try:
        question = item.get("question", {})
        author = item.get("author", {})
        created = item.get("created_time", 0)
        answer_id = str(item.get("id", ""))
        question_id = str(question.get("id", ""))

        return {
            "id": answer_id,
            "question_id": question_id,
            "title": question.get("title", "无标题"),
            "author": author.get("name", uid) if isinstance(author, dict) else uid,
            "voteup_count": item.get("voteup_count", 0),
            "comment_count": item.get("comment_count", 0),
            "date": datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "",
            "url": f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}",
            "kind": "answer",
            "content_md": html_to_md(item.get("content", "")),
        }
    except Exception as e:
        print(f"      [!] Parse answer error: {e}")
        return None


def _parse_article_item(item: dict, uid: str) -> Optional[dict]:
    """Parse a single article API response into a unified item dict."""
    try:
        author = item.get("author", {})
        created = item.get("created", 0) or item.get("created_time", 0)
        article_id = str(item.get("id", ""))

        return {
            "id": article_id,
            "title": item.get("title", "无标题"),
            "author": author.get("name", uid) if isinstance(author, dict) else uid,
            "voteup_count": item.get("voteup_count", 0),
            "comment_count": item.get("comment_count", 0),
            "like_count": item.get("like_count", 0),
            "date": datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "",
            "url": f"https://zhuanlan.zhihu.com/p/{article_id}",
            "kind": "article",
            "content_md": html_to_md(item.get("content", "")),
        }
    except Exception as e:
        print(f"      [!] Parse article error: {e}")
        return None


# ---------------------------------------------------------------------------
# Index management (incremental crawl)
# ---------------------------------------------------------------------------
def _load_index(index_path: str) -> list:
    """Load existing crawl index. Returns list of seen item IDs."""
    if not os.path.exists(index_path):
        return []
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # v2.x index was list of item dicts (old format).
            # v3.0 index is list of strings (IDs only, cleaner).
            if data and isinstance(data[0], dict):
                return [i.get("id", "") for i in data]
            return [str(id_) for id_ in data]
    except (json.JSONDecodeError, IndexError, OSError):
        return []


def _save_index(index_path: str, index: list):
    """Save crawl index (list of item IDs, in crawl order)."""
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _index_path(output_dir: str, kind: str) -> str:
    return os.path.join(output_dir, f".index_{kind}.json")


# ---------------------------------------------------------------------------
# File writing (yaml frontmatter + markdown)
# ---------------------------------------------------------------------------
def _escape_yaml_value(s: str) -> str:
    """Escape a string for YAML double-quoted value."""
    # Escape backslashes and double-quotes
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return s


def _save_output_file(item: dict, output_dir: str) -> Optional[str]:
    """Save a single item as yaml-frontmatter + Markdown file.

    Frontmatter uses Chinese field names to match the old zhihubf format:
      标题 / 作者 / 日期 / 链接 / 类型 / 标签 / 摘要
    Filenames use question title (truncated to 80 chars) not raw ID.
    Content header: # [QUESTION_TITLE](url)
                    ---
                   answer text...
    """
    title = str(item.get("title", "无标题"))
    # Truncate title to 80 chars for filename, replace unsafe chars
    safe_title = re.sub(r'[\*/?:"<>|]', "_", title)
    author = str(item.get("author", ""))
    tags = item.get("tags", "")
    summary = item.get("summary", "")
    kind = item.get("kind", "answer")
     # OLD format used "answrER" (capital ER), preserve that for compatibility
    if kind == "answer":
        kind = "answrER"
    file_prefix = "回答" if kind == "answrER" else "文章"

    # Filename
    basename = f"{file_prefix}_{safe_title[:80]}.md"
    filepath = os.path.join(output_dir, basename)

    if os.path.exists(filepath):
        return None

    # Frontmatter (Chinese keys, quoted values)
    fm_lines = [
        "---",
        f'标题: "{_escape_yaml_value(title)}"',
        f'作者: "{_escape_yaml_value(author)}"',
        f"日期: \"{item.get('date', '')}\"",
        f'链接: "{item.get("url", "")}"',
        f'类型: "{kind}"',
        f'标签: "{tags}"',
        f'摘要: "{_escape_yaml_value(summary)}"',
        "---",
    ]

    # Content: heading + separator + content separator + body
    content = "\n".join(fm_lines) + f"\n\n# [{title}]({item.get('url', '')})\n\n---\n\n" + item.get("content_md", "") + "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return basename


# ---------------------------------------------------------------------------
# Main crawl engine
# ---------------------------------------------------------------------------
def crawl_single_page(session: requests.Session, url: str, params: dict, kind: str) -> tuple:
    """Fetch one page. Returns (items, total, is_end)."""
    from urllib.parse import urlencode

    full_url = f"{url}?{urlencode(params, safe='*')}"

    # Max 3 retries with exponential backoff for transient errors
    for attempt in range(3):
        try:
            resp = session.get(full_url, timeout=15)
        except requests.RequestException as e:
            print(f"       [!] Network error (attempt {attempt+1}/3): {e}")
            time.sleep(2 ** attempt)
            continue

        # Cookie/session expired - immediate 401/403
        if resp.status_code in (401, 403, 404):
            # On first attempt, report it. On retry (attempt > 0), still report and break.
            if attempt == 0:
                msg_map = {401: "401 Unauthorized - cookie may have expired",
                        403: "403 Forbidden - cookie may have expired",
                        404: "404 Not Found - API endpoint may have changed"}
                print(f"       [!] {msg_map.get(resp.status_code, f'HTTP {resp.status_code}')}")
            break

        if resp.status_code != 200:
            print(f"       [!] HTTP {resp.status_code}: {resp.text[:200]}")
            return [], 0, True

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            print(f"       [!] JSON decode error: {e}")
            return [], 0, True

        # API-level errors (not HTTP)
        if "error" in data:
            err_msg = data.get("error", {}).get("message", data["error"])
            if isinstance(data["error"], dict):
                err_msg = data["error"].get("message", str(data["error"]))
            else:
                err_msg = str(data["error"])

            # Known auth errors - don't retry
            if "无此操作权限" in err_msg or "登录" in err_msg or "auth" in err_msg.lower():
                print(f"       [!] API auth error: {err_msg}")
                break

            print(f"       [!] API error: {err_msg}")
            break

        items = data.get("data", [])
        paging = data.get("paging", {})
        total = paging.get("totals", 0)
        is_end = paging.get("is_end", True)
        return items, total, is_end

    # All attempts exhausted
    return [], 0, True


def crawl_content(kind: str = "answer",
                user_id: str = "",
                output_dir: str = "./output",
                cookie_file: str = "",
                max_items: int = 0,
                stop_check: Optional[Callable] = None,
                pages_to_fetch: int = 0
                 ) -> int:
    """
    Main crawl loop for a given user.

    Args:
        kind: 'answer' or 'article'
        user_id: Zhihu username (required; overrides config.json)
        output_dir: Directory to save markdown files
        cookie_file: Path to cookie JSON file (empty = use config default)
        max_items: Max items to crawl (0 = all)
        stop_check: Optional callback that returns True to abort
        pages_to_fetch: If > 0, limit to this many pages

    Returns:
        Number of items crawled and saved
    """
    # Use config defaults for empty params
    if not cookie_file:
        cookie_file = CONFIG_COOKIE_FILE
    if not user_id:
        raise ValueError("user_id is required. Pass --user <USERNAME> from run.py")

    if not os.path.exists(cookie_file):
        print(f"[!] Cookie file not found: {cookie_file}")
        return 0

    # Load cookies
    cookies_dict = load_cookies_from_json(cookie_file)
    session = cookies_to_requests_session(cookies_dict)

    cfg = CONTENT_CONFIGS[kind]
    total_crawled = 0
    seen_ids = set()

    # Ensure output dir
    os.makedirs(output_dir, exist_ok=True)

    # Load index from previous crawl (incremental)
    index_path = _index_path(output_dir, kind)
    old_index = _load_index(index_path)
    seen_ids = set(str(i) for i in old_index)
    total_existing = len(seen_ids)

    print(f"\n{'='*60}")
    print(f"  User: {user_id} | {cfg['label'].upper()} CRAWL")
    print(f"{'='*60}")
    print(f"Cookie file: {cookie_file}")
    print(f"Existing index: {total_existing} items")
    print(f"Target max items: {'all' if max_items == 0 else max_items}")

    # Fetch loop
    page_num = 0
    offset = 0
    total = 0
    stop = False

    while not stop:
        page_num += 1

        # Check stop
        if stop_check and stop_check():
            stop = True
            break

        # Check page limit
        if pages_to_fetch > 0 and page_num > pages_to_fetch:
            break

        # Check total item limit
        if max_items > 0 and total_crawled >= max_items:
            break

        print(f"\nFetching page {page_num}: offset={offset}...", end=" ", flush=True)

        params = cfg["params"].copy()
        params["offset"] = offset
        params["limit"] = 20

        # Substitute {uid} placeholder in URL (e.g., {uid} -> the specified user)
        api_url = cfg["api_url"].format(uid=user_id, kind=kind)
        items, total, is_end = crawl_single_page(session, api_url, params, kind)

        if total > 0 and total_crawled == 0:
            print(f"API indicates {total} total")

        if not items or stop:
            if stop:
                break
            print("No data or stop requested")
            break

        # Filter by seen IDs (incremental)
        new_items = []
        for item in items:
            item_id = str(item.get("id", ""))
            if item_id in seen_ids:
                continue
            parsed = _parse_article_item(item, uid) if kind == "article" else _parse_answer_item(item, uid)
            if parsed:
                new_items.append(parsed)
                seen_ids.add(parsed["id"])

        if not new_items:
            print("All seen in index, continuing...")
        else:
            # Save items
            saved_count = 0
            for parsed in new_items:
                if max_items > 0 and total_crawled >= max_items:
                    break

                try:
                    filename = _save_output_file(parsed, output_dir)
                    if filename:
                        total_crawled += 1
                        saved_count += 1
                except Exception as e:
                    print(f"\n      [!] Save failed for {parsed['id']}: {e}")

            if saved_count > 0:
                print(f"{len(items)} items, {saved_count} new (total: {total_crawled}/{total if total > 0 else '...'})")
            else:
                print(f"{len(items)} items, all seen in index")

        # Update index
        new_ids = [str(i["id"]) for i in new_items]
        if new_ids:
            _save_index(index_path, old_index + new_ids)
            old_index.extend(new_ids)

        # Check end / limit
        if is_end or stop:
            break
        if pages_to_fetch > 0 and page_num >= pages_to_fetch:
            break
        if max_items > 0 and total_crawled >= max_items:
            break

        # Rate limiting / jitter between pages
        wait = random.uniform(2, 5)
        jitter = random.uniform(-0.5, 1.0)
        wait = max(1.5, wait + jitter)
        time.sleep(wait)

        offset += 20

    elapsed = time.time()
    status = "terminated" if stop else "completed"
    print(f"\n{'='*50}")
    print(f"  {cfg['label'].title()} crawl {status}")
    print(f"  Crawled: {total_crawled} | Pages: {page_num} | Offset: {offset}")
    if total:
        print(f"  Progress: {total_crawled}/{total}")
    print(f"  Dir: {output_dir}")
    print(f"{'='*50}")

    return total_crawled


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Zhihu Crawler v3.0 (HTTP requests edition)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--kind", "-k", choices=["answer", "article"],
                    default="answer", help="Content type to crawl")
    parser.add_argument("--output", "-o", default="./output",
                    help="Output directory")
    parser.add_argument("--max", "-m", type=int, default=0,
                    help="Max items to crawl (0=all)")
    parser.add_argument("--pages", "-p", type=int, default=0,
                    help="Max pages to fetch (0=auto until end)")
    parser.add_argument("--cookie", "-c", default=COOKIE_FILE,
                    help="Cookie JSON file path")
    args = parser.parse_args()

    crawl_content(
        kind=args.kind,
        output_dir=args.output,
        cookie_file=args.cookie,
        max_items=args.max,
        pages_to_fetch=args.pages,
    )


if __name__ == "__main__":
    main()
