"""
ZhihuSpider - 知乎用户回答导出工具

一键导出知乎用户的全部回答，保存为 Markdown 文件。

使用方法:
  GUI 模式（默认）: python main.py
  CLI 模式:         python main.py --cli

GitHub: https://github.com/lemoabc/ZhihuSpider
"""
import sys

__version__ = "1.0.0"


def cli_main():
    """命令行模式：读取 config.json，自动爬取。"""
    import json
    import os
    import re
    import time

    from DrissionPage import Chromium, ChromiumOptions
    from crawler import crawl_answers

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

    DEFAULT_CONFIG = {
        "targets": ["https://www.zhihu.com/people/xubinlvshi/answers"],
        "output_dir": "./output",
        "page_delay_min": 8,
        "page_delay_max": 15,
        "max_answers": 0,
    }

    # 加载配置
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] 未找到配置文件，已自动生成: {CONFIG_PATH}")
        print("    请编辑 config.json 中的 targets 填入目标用户 URL，然后重新运行。\n")
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        sys.exit(0)

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    if not config.get('targets'):
        print("[!] config.json 中 targets 为空，请填入至少一个目标 URL。")
        sys.exit(1)

    targets = config['targets']
    output_base = config.get('output_dir', './output')
    if not os.path.isabs(output_base):
        output_base = os.path.normpath(os.path.join(BASE_DIR, output_base))
    delay_min = config.get('page_delay_min', 8)
    delay_max = config.get('page_delay_max', 15)
    max_answers = config.get('max_answers', 0)

    def extract_user_id(url: str) -> str:
        match = re.search(r'zhihu\.com/people/([^/?#]+)', url)
        if match:
            return match.group(1).rstrip('/')
        clean = url.strip().strip('/')
        if clean and not clean.startswith('http'):
            return clean
        print(f"[!] 无法识别的 URL 格式: {url}")
        return ''

    user_ids = [uid for url in targets if (uid := extract_user_id(url))]
    if not user_ids:
        print("[!] 未找到有效的目标用户，请检查 config.json。")
        sys.exit(1)

    print("=" * 60)
    print(f"  ZhihuSpider v{__version__} (CLI)")
    print(f"  目标用户: {', '.join(user_ids)}")
    print(f"  爬取数量: {'全部' if max_answers == 0 else f'每人最多 {max_answers} 条'}")
    print(f"  翻页间隔: {delay_min}-{delay_max} 秒")
    print(f"  输出目录: {output_base}")
    print("=" * 60)

    def wait_for_login(tab, timeout=300):
        print("\n  请在弹出的浏览器窗口中登录知乎（扫码或账号密码）")
        print("  登录成功后脚本会自动继续...")
        print(f"  （最多等待 {timeout // 60} 分钟）\n")
        start = time.time()
        tick = 0
        while time.time() - start < timeout:
            tick += 1
            try:
                cookies = tab.cookies()
                names = [c.get('name', '') for c in cookies] if cookies else []
                if 'z_c0' in names:
                    print("  >> 登录成功！")
                    return True
                if 'signin' not in tab.url and 'sign-in' not in tab.url:
                    if tab.ele('css:.AppHeader-profileEntry', timeout=2):
                        print("  >> 登录成功！")
                        return True
                if tick % 4 == 0:
                    print(f"  >> 等待登录中... ({int(time.time() - start)} 秒)")
            except Exception:
                pass
            time.sleep(5)
        print("  >> 等待登录超时")
        return False

    def ensure_login(browser):
        tab = browser.latest_tab
        tab.get('https://www.zhihu.com/')
        time.sleep(3)
        logged_in = False
        try:
            cookies = tab.cookies()
            names = [c.get('name', '') for c in cookies] if cookies else []
            logged_in = 'z_c0' in names
        except Exception:
            pass
        if logged_in:
            print("  已处于登录状态，无需重复登录。")
        else:
            tab.get('https://www.zhihu.com/signin')
            time.sleep(2)
            if not wait_for_login(tab):
                return None
        time.sleep(2)
        return tab

    print("\n[1] 启动浏览器...")
    co = ChromiumOptions()
    co.auto_port(True)
    co.set_argument('--disable-blink-features=AutomationControlled')
    browser = Chromium(co)

    print("\n[2] 检查登录状态...")
    tab = ensure_login(browser)
    if tab is None:
        print("\n[!] 登录失败，退出。")
        browser.quit()
        sys.exit(1)

    total_saved = 0
    for i, user_id in enumerate(user_ids, 1):
        print(f"\n{'#' * 60}")
        print(f"  [{i}/{len(user_ids)}] 开始爬取用户: {user_id}")
        print(f"{'#' * 60}")
        user_output_dir = os.path.join(output_base, user_id)
        saved = crawl_answers(
            tab=tab, user_id=user_id, output_dir=user_output_dir,
            max_answers=max_answers, delay_range=(delay_min, delay_max),
        )
        total_saved += saved
        if i < len(user_ids):
            print("\n  切换用户前等待 10 秒...")
            time.sleep(10)

    print(f"\n{'=' * 60}")
    print(f"  全部完成！共爬取 {len(user_ids)} 个用户，保存 {total_saved} 条回答")
    print(f"  输出目录: {output_base}")
    print(f"{'=' * 60}")
    browser.quit()


if __name__ == '__main__':
    if '--cli' in sys.argv:
        cli_main()
    else:
        from gui import run_gui
        run_gui()
