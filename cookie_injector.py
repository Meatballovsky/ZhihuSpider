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

Cookie injection module for Zhihu Crawler -- CDP via WebSocket protocol.

This script connects to a running Edge/Chrome browser via CDP WebSocket and
manages cookies using the Network domain commands.

Configuration:
    Reads from config.local.json (or config.json) at project root.

Usage:
    source venv/bin/activate
    python cookie_injector.py --help

     # Export cookies from Edge to JSON file
    python cookie_injector.py --export-cookies cookies.json

     # Inject cookies from JSON file into browser
    python cookie_injector.py

Prerequisite:
    Start Edge with CDP enabled first (see README.md).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import urllib.request

# Load config - prefer config.local.json, fallback to config.json
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.local.json")
if not os.path.isfile(_CONFIG_PATH):
      _CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
      _CONFIG = json.load(_f)

CDP_PORT = _CONFIG.get("cdp_port", 9222)

WS_BASE = None
CMD_ID = 0


def _cdp_init(port: int):
    """Initialize WebSocket connection to CDP browser."""
    global WS_BASE, CMD_ID
    try:
        url = f"http://127.0.0.1:{port}/json"
        with urllib.request.urlopen(url, timeout=5) as resp:
            pages = json.loads(resp.read())
        if not pages:
            raise ConnectionError("No tabs found on CDP port")
        ws_url = pages[0].get("webSocketDebuggerUrl")
        if not ws_url:
            raise ConnectionError("No WebSocket debugger URL in /json response")
        WS_BASE = ws_url
        CMD_ID = 0
    except Exception as e:
        raise ConnectionError(
            f"CDP connection failed (port {port}): {e}\n"
            "Make sure agent_edge_launcher has started Edge on port 9222"
        )


async def _cdp_send(method: str, params: dict = None) -> dict:
    """Send a CDP command via WebSocket and return the response."""
    global CMD_ID
    CMD_ID += 1
    import websockets
    msg = {"id": CMD_ID, "method": method, "params": params or {}}
    try:
        async with websockets.connect(WS_BASE, ping_interval=None) as ws:
            await ws.send(json.dumps(msg))
            recv = await ws.recv()
            result = json.loads(recv)
            if "error" in result:
                raise Exception(f"CDP error ({method}): {result['error']}")
        return result.get("result", {})
    except Exception as e:
        raise ConnectionError(f"CDP command {method} failed: {e}")


def export_cookies(target_path: str, cdp_port: int = 9222, domain: str = ".zhihu.com") -> list:
    """
    Extract cookies from the browser and export to JSON file.

    Args:
        target_path: Output JSON file path.
        cdp_port: CDP port (default 9222).
        domain: Filter cookies by domain.

    Returns:
        List of extracted cookies.
    """
    _cdp_init(cdp_port)

    raw = asyncio.run(_cdp_send("Network.getAllCookies"))
    raw_cookies = raw.get("cookies", [])
    print(f"   Total cookies from Edge: {len(raw_cookies)}")

    target_cookies = []
    for c in raw_cookies:
        if domain in c.get("domain", ""):
            target_cookies.append({
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ""),
                "path": c.get("path", "/"),
                "secure": c.get("secure", False),
                "httpOnly": c.get("httpOnly", False),
                "sameSite": c.get("sameSite", "None"),
            })

    print(f"   Zhihu cookies found: {len(target_cookies)}")

    if not target_cookies:
        print("   WARNING: No Zhihu cookies found!")
        print("   Make sure you are logged into zhihu.com in Edge.")
        return []

    os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(target_cookies, f, ensure_ascii=False, indent=2)

    print(f"   Exported to: {target_path}")
    return target_cookies


def inject_cookies(cookie_file: str, cdp_port: int = 9222) -> list:
    """
    Inject cookies from a JSON file into the browser via CDP.

    Args:
        cookie_file: Path to JSON file with cookie objects.
        cdp_port: CDP port (default 9222).

    Returns:
        List of successfully injected cookie names.
    """
    _cdp_init(cdp_port)

    if not os.path.isfile(cookie_file):
        raise FileNotFoundError(f"Cookie file not found: {cookie_file}")

    with open(cookie_file, "r", encoding="utf-8") as f:
        cookie_list = json.load(f)

    print(f"   Cookies to inject: {len(cookie_list)}")

    print("   Navigating to zhihu.com...")
    asyncio.run(_cdp_send("Page.navigate", {"url": "https://www.zhihu.com"}))
    time.sleep(3)

    injected = []
    for c in cookie_list:
        try:
            asyncio.run(_cdp_send("Network.setCookie", {
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ".zhihu.com"),
                "path": c.get("path", "/"),
                "secure": c.get("secure", False),
                "httpOnly": c.get("httpOnly", False),
                "sameSite": c.get("sameSite", "None"),
            }))
            injected.append(c["name"])
        except Exception as e:
            print(f"   Failed to inject '{c['name']}': {e}")

    print("   Reloading page...")
    asyncio.run(_cdp_send("Page.reload", {"ignoreCache": True}))
    time.sleep(2)

    return injected


def main():
    parser = argparse.ArgumentParser(
        description="Zhihu cookie injector/extractor via CDP WebSocket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Export cookies from Edge to JSON file
    python cookie_injector.py --export-cookies /tmp/zhihu-scraper/.local/cookies.json

    # Inject cookies from JSON into browser
    python cookie_injector.py

    # Custom port
    python cookie_injector.py --cdp-port 9223
        """,
    )

    parser.add_argument(
        "--export-cookies",
        type=str,
        default=None,
        help="Export cookies from browser to JSON file",
    )
    parser.add_argument(
        "--import-cookies",
        type=str,
        default="/tmp/zhihu-scraper/.local/cookies.json",
        help="Import cookies from JSON file",
    )
    parser.add_argument(
        "--cdp-port",
        type=int,
        default=9222,
        help="CDP port (default: 9222, from agent_edge_launcher)",
    )

    args = parser.parse_args()

    if args.export_cookies:
        cookies = export_cookies(args.export_cookies, args.cdp_port)
        if not cookies:
            print("\nNo Zhihu cookies found. Make sure you are logged in to zhihu.com in Edge.")
            sys.exit(1)
        return 0

    else:
        cookie_file = args.import_cookies
        if not os.path.isfile(cookie_file):
            print(f"Cookie file {cookie_file} not found!")
            print("\nFirst run this to create the file:")
            print(f"  python cookie_injector.py --export-cookies {cookie_file}\n")
            print("Or login to zhihu.com in Edge first, then export cookies.")
            sys.exit(1)

        with open(cookie_file, "r") as f:
            cookie_list = json.load(f)
        print(f"Injecting {len(cookie_list)} cookies into Edge...")
        injected = inject_cookies(cookie_file, args.cdp_port)
        print(f"Successfully injected {len(injected)} cookies")
        return 0


if __name__ == "__main__":
    sys.exit(main())
