"""Cross-platform Chromium browser detection."""
import os
import platform

_SYSTEM = platform.system()

_MAC_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

_LINUX_PATHS = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/microsoft-edge",
    "/usr/bin/brave-browser",
]

_WIN_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application msedge.exe",
]

_ALL_PATHS = _MAC_PATHS + _WIN_PATHS + _LINUX_PATHS


def find_browser() -> str:
    """Find and return the path to any installed Chromium browser."""
    paths = _ALL_PATHS
    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None
