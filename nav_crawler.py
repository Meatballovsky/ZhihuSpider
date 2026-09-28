#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
# 🤖 AGENT PROJECT METADATA
# Project ID:   zhihubf
# Registry:     ~/agent_projects/projects.json
# Manifest:     ~/agent_projects/zhihubf/metadata.json
# Version:      4.0.0
# Status:       Stable
# Owner:        Agent/User
================================================================================

Zhihu browser-navigation crawler (v4 engine) — 2026-09 风控适配版。

为什么需要 v4：知乎对 XHR 型请求强制 x-zse-93/96 签名（裸 requests / 页内
fetch 一律 403 code 40362），但**浏览器顶层导航**到 API URL 免签、带登录
cookie 直接返回纯 JSON。本引擎用 Playwright 驱动系统安装的 Chromium 系
浏览器逐页导航抓取，天然携带浏览器指纹，无需任何签名逆向。

隐私设计（重要）：
  * 只复制浏览器 Cookie SQLite 中 host_key 属于 zhihu/zhimg 的行，
    密码、历史、扩展、其他站点 cookie 一律不出目录。
  * 副本用 sqlite backup API 做原子快照（浏览器开着也安全），
    再原地 DELETE 非知乎行——保留原行字节，不重建。
  * 临时 profile 用完即删（--keep-profile 可保留调试）。

跨机器说明：
  * Cookie 加密密钥绑定"这台机器 + 这个系统用户 + 这个浏览器"（macOS 钥匙串 /
    Windows DPAPI），profile 副本方案只在登录过知乎的本机有效。
  * 换机器：在目标机器装任意 Chromium 系浏览器并登录知乎即可；或
    --cookie-file 用导出的 cookie（fresh profile + add_cookies，全平台通用）。

Usage:
    python nav_crawler.py --user <URL_TOKEN> [--kind answer|article]
                          [--max N] [--pages N] [--browser auto|edge|chrome]
                          [--cookie-file cookies.json] [--output DIR]
                          [--headful] [--keep-profile]
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import shutil
import sqlite3
import sys
import tempfile
import time
from urllib.parse import quote

# 复用 v3 的解析/落盘/索引逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crawler import (  # noqa: E402
    CONTENT_CONFIGS,
    _parse_answer_item,
    _parse_article_item,
    _save_output_file,
    _save_index,
    _load_index,
)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("需要 playwright: pip install playwright（无需 playwright install，使用系统浏览器）")

HOME = os.path.expanduser("~")
ALLOWED_HOST_SUFFIXES = ("zhihu.com", "zhimg.com")

BROWSERS = {
    "edge": {
        "channel": "msedge",
        "darwin": {
            "exe": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "profile": os.path.join(HOME, "Library/Application Support/Microsoft Edge"),
        },
        "linux": {
            "exe": "/opt/microsoft/msedge/msedge",
            "profile": os.path.join(HOME, ".config/microsoft-edge"),
        },
        "win32": {
            "exe": os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            "profile": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
        },
    },
    "chrome": {
        "channel": "chrome",
        "darwin": {
            "exe": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "profile": os.path.join(HOME, "Library/Application Support/Google/Chrome"),
        },
        "linux": {
            "exe": "/usr/bin/google-chrome",
            "profile": os.path.join(HOME, ".config/google-chrome"),
        },
        "win32": {
            "exe": os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            "profile": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        },
    },
}


def _platform_key() -> str:
    if sys.platform == "win32":
        return "win32"
    return "darwin" if platform.system() == "Darwin" else "linux"


def find_browser(pref: str = "auto"):
    """返回 (name, exe_path, profile_dir)；auto 按 edge → chrome 顺序探测。"""
    key = _platform_key()
    names = ["edge", "chrome"] if pref == "auto" else [pref]
    for n in names:
        loc = BROWSERS[n][key]
        if os.path.isfile(loc["exe"]) and os.path.isdir(loc["profile"]):
            return n, loc["exe"], loc["profile"]
    raise SystemExit(f"未找到可用浏览器（{pref}）。请安装 Edge/Chrome 或用 --browser 指定。")


def _cookie_db_path(profile_dir: str, profile_name: str) -> tuple:
    """返回 (绝对路径, 相对 profile 根的布局路径)。新老浏览器布局不同：
    Chromium 新式在 Network/Cookies，旧式/部分 Edge 直接在 Default/Cookies，
    副本必须写到与源相同的相对位置，否则启动的浏览器根本不看那个文件。"""
    base = os.path.join(profile_dir, profile_name)
    for rel in (os.path.join("Network", "Cookies"), "Cookies"):
        p = os.path.join(base, rel)
        if os.path.isfile(p):
            return p, rel
    raise SystemExit(f"在 {base} 下找不到 Cookies 数据库（--profile-name 对吗？默认 Default）")


def extract_zhihu_cookies(profile_dir: str, profile_name: str, dest_dir: str) -> int:
    """只保留知乎域名的 cookie 到独立 profile；其他站点 cookie/密码/历史不碰。

    用 SQLite backup API 做原子快照（浏览器运行中也安全——直接拷文件会
    拷到写一半的页导致库损坏），再原地 DELETE 非知乎行：保留原行字节，
    避免重建行时丢字段/编码差异。"""
    src, rel = _cookie_db_path(profile_dir, profile_name)
    dst_db = os.path.join(dest_dir, profile_name, rel)
    os.makedirs(os.path.dirname(dst_db), exist_ok=True)

    s = sqlite3.connect(src)
    d = sqlite3.connect(dst_db)
    s.backup(d)
    s.close()
    like_clauses = " OR ".join(["host_key LIKE ?"] * len(ALLOWED_HOST_SUFFIXES))
    like_params = [f"%{h}%" for h in ALLOWED_HOST_SUFFIXES]
    total = d.execute("SELECT COUNT(*) FROM cookies").fetchone()[0]
    d.execute(f"DELETE FROM cookies WHERE NOT ({like_clauses})", like_params)
    kept = d.execute("SELECT COUNT(*) FROM cookies").fetchone()[0]
    d.commit()
    d.close()

    # Local State：Windows/Linux 的 cookie 加密钥匙在这里（macOS 在钥匙串），一并带上
    ls = os.path.join(profile_dir, "Local State")
    if os.path.isfile(ls):
        shutil.copy2(ls, os.path.join(dest_dir, "Local State"))
    print(f"  源库 {total} 条 cookie → 保留知乎域 {kept} 条")
    return kept


def api_page(page, url: str) -> dict:
    """浏览器顶层导航取 JSON（免 x-zse 签名）。"""
    resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
    body = resp.text()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        i, j = body.find("{"), body.rfind("}")
        if 0 <= i < j:
            data = json.loads(body[i:j + 1])
        else:
            raise RuntimeError(f"非 JSON 响应（可能被风控/重定向）: {body[:160]}")
    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        raise RuntimeError(f"API 错误 {err.get('code')}: {err.get('message', '')[:80]}")
    return data


def crawl(page, user: str, kind: str, output_dir: str, max_items: int = 0, pages: int = 0,
          delay_min: float = 2.0, delay_max: float = 5.0, retry_max: int = 3) -> int:
    cfg = CONTENT_CONFIGS[kind]
    os.makedirs(output_dir, exist_ok=True)
    index_path = os.path.join(output_dir, cfg["index_file"])
    if not os.path.exists(index_path):
        # 继承旧版存档索引：v2.x 用中文文件名（.index_回答.json）且可能放在上级目录。
        # 找到即合并进新索引，避免对着老存档重复抓 1000+ 条。
        for legacy in (os.path.join(output_dir, f".index_{cfg['label']}.json"),
                       os.path.join(os.path.dirname(output_dir.rstrip("/")), f".index_{cfg['label']}.json")):
            if os.path.exists(legacy):
                old_index = _load_index(legacy)
                _save_index(index_path, old_index)
                print(f"已继承旧索引 {legacy}（{len(old_index)} 条）")
                break
        else:
            old_index = []
    else:
        old_index = _load_index(index_path)
    seen_ids = set(old_index)
    print(f"用户: {user} | 类型: {cfg['label']} | 已有索引: {len(old_index)} 条 | 上限: {max_items or '全部'}")

    params = cfg["params"].copy()
    url = (cfg["api_url"].format(uid=user, kind=kind)
           + "?include=" + quote(params["include"])
           + "&limit=20&offset=0&sort_by=" + params["sort_by"])

    # 预热：先访问知乎首页。直接以 API URL 作为首个导航会被判为
    # "第三方独立请求"（Sec-Fetch-Site: none → 10003/602）；同源链建立后再导航即 200。
    page.goto("https://www.zhihu.com/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(2)

    total_crawled = 0
    page_num = 0
    while True:
        page_num += 1
        if pages > 0 and page_num > pages:
            break
        if max_items > 0 and total_crawled >= max_items:
            break
        print(f"  第 {page_num} 页 ...", end=" ", flush=True)

        data = None
        for attempt in range(retry_max):
            try:
                data = api_page(page, url)
                break
            except Exception as e:
                print(f"[重试 {attempt + 1}/{retry_max}: {e}]", end=" ", flush=True)
                time.sleep(5 * (attempt + 1))
        if data is None:
            print("放弃本页")
            break

        items = data.get("data", [])
        paging = data.get("paging", {})
        new_items = []
        for item in items:
            if str(item.get("id", "")) in seen_ids:
                continue
            parsed = _parse_article_item(item, user) if kind == "article" else _parse_answer_item(item, user)
            if parsed:
                new_items.append(parsed)
                seen_ids.add(parsed["id"])

        saved_ids = []
        for parsed in new_items:
            if max_items > 0 and total_crawled >= max_items:
                break
            if _save_output_file(parsed, output_dir):
                total_crawled += 1
                saved_ids.append(str(parsed["id"]))
        saved = len(saved_ids)
        # 只索引真正落盘的条目：被 max 截断未保存的 id 不能进索引，否则永久丢失
        if saved_ids:
            old_index = old_index + saved_ids
            _save_index(index_path, old_index)
        print(f"{len(items)} 条, 新增 {saved} (累计 {total_crawled})")

        if paging.get("is_end") or not items or not paging.get("next"):
            break
        url = paging["next"].replace("http://", "https://")
        # 限速：显式参数驱动（修复 v3 的 config 死配置）+ 抖动
        time.sleep(max(1.5, random.uniform(delay_min, delay_max) + random.uniform(-0.5, 1.0)))

    print(f"完成: {total_crawled} 条 → {output_dir}")
    return total_crawled


def main():
    ap = argparse.ArgumentParser(description="知乎浏览器导航式爬虫 v4")
    ap.add_argument("--user", required=True, help="目标用户 url_token（个人主页 URL 末段）")
    ap.add_argument("--kind", choices=["answer", "article"], default="answer")
    ap.add_argument("--max", type=int, default=0, help="最多抓取条数（0=全部）")
    ap.add_argument("--pages", type=int, default=0, help="最多翻页数（0=直到结尾）")
    ap.add_argument("--output", default=None, help="输出目录（默认 ~/Desktop/zhihubf/<user>）")
    ap.add_argument("--browser", default="auto", choices=["auto", "edge", "chrome"])
    ap.add_argument("--profile-name", default="Default", help="浏览器 profile 目录名")
    ap.add_argument("--cookie-file", default=None,
                    help="跨机器方案：使用导出的 cookie JSON（fresh profile + add_cookies）")
    ap.add_argument("--delay-min", type=float, default=2.0)
    ap.add_argument("--delay-max", type=float, default=5.0)
    ap.add_argument("--headful", action="store_true", help="显示浏览器窗口（调试）")
    ap.add_argument("--keep-profile", action="store_true", help="保留临时 profile（调试）")
    args = ap.parse_args()

    output = args.output or os.path.join(HOME, "Desktop", "zhihubf", args.user)
    os.makedirs(output, exist_ok=True)

    name, exe, profile_dir = find_browser(args.browser)
    tmpdir = tempfile.mkdtemp(prefix=f"zhihu-nav-{name}-")
    print(f"浏览器: {name} | 临时 profile: {tmpdir}")

    channel = BROWSERS[name]["channel"]
    # Playwright 默认注入 --use-mock-keychain：浏览器会用假密钥，真实 profile 复制来的
    # 加密 cookie 全部解密失败被静默丢弃（jar=0 的元凶）—— 必须忽略这两个默认参数
    IGNORE_DEFAULT = ["--use-mock-keychain", "--password-store=basic"]
    with sync_playwright() as p:
        if args.cookie_file:
            # 跨机器路径：空 profile + 注入导出 cookie
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=tmpdir, channel=channel, headless=not args.headful,
                ignore_default_args=IGNORE_DEFAULT,
                args=["--disable-blink-features=AutomationControlled", "--disable-extensions"])
            with open(args.cookie_file) as f:
                raw = json.load(f)
            cookies = [{k: c[k] for k in ("name", "value", "domain", "path") if k in c}
                       for c in raw]
            ctx.add_cookies(cookies)
            print(f"已注入 {len(cookies)} 条导出 cookie")
        else:
            kept = extract_zhihu_cookies(profile_dir, args.profile_name, tmpdir)
            print(f"已复制知乎域 cookie {kept} 行（其余站点 cookie/密码/历史未复制）")
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=tmpdir, channel=channel, headless=not args.headful,
                ignore_default_args=IGNORE_DEFAULT,
                args=["--disable-blink-features=AutomationControlled", "--disable-extensions"])

        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # Playwright headless 默认 UA 含 "HeadlessChrome"，知乎服务端直接封 —— 洗成正常 UA；
        # Referer 必须是纯 zhihu 首页（同源判定），否则 api/v4 判为"第三方应用独立请求" 401/602
        clean_ua = page.evaluate("navigator.userAgent").replace("HeadlessChrome", "Chrome")
        page.set_extra_http_headers({
            "User-Agent": clean_ua,
            "Referer": "https://www.zhihu.com/",
        })
        try:
            crawl(page, args.user, args.kind, output, args.max, args.pages,
                  args.delay_min, args.delay_max)
        finally:
            ctx.close()
            if not args.keep_profile:
                shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
