"""自动检测本地 Chromium 内核浏览器。"""
import os
import shutil

_CANDIDATES = [
    (
        "Chrome",
        [
            r"Google\Chrome\Application\chrome.exe",
        ],
        ["chrome", "google-chrome"],
    ),
    (
        "Edge",
        [
            r"Microsoft\Edge\Application\msedge.exe",
        ],
        ["msedge"],
    ),
    (
        "360安全浏览器",
        [
            r"360Chrome\Chrome\Application\360chrome.exe",
            r"360se6\Application\360se.exe",
        ],
        [],
    ),
    (
        "QQ浏览器",
        [
            r"Tencent\QQBrowser\QQBrowser.exe",
        ],
        [],
    ),
]

_PROGRAM_ROOTS = [
    os.environ.get("ProgramFiles", r"C:\Program Files"),
    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    os.environ.get("LOCALAPPDATA", ""),
    os.path.join(os.environ.get("APPDATA", ""), "..\\Local"),
]


def find_browser() -> tuple:
    """查找本地 Chromium 内核浏览器。

    Returns:
        (exe_path, browser_name) 找到时返回路径和名称；
        (None, "") 未找到。
    """
    for name, rel_paths, which_names in _CANDIDATES:
        for root in _PROGRAM_ROOTS:
            if not root:
                continue
            for rel in rel_paths:
                full = os.path.normpath(os.path.join(root, rel))
                if os.path.isfile(full):
                    return full, name
        for cmd in which_names:
            found = shutil.which(cmd)
            if found:
                return found, name
    return None, ""
