"""爬虫工作线程，在 QThread 中运行，通过信号与 GUI 通信。"""
import io
import os
import re
import sys
import time
import threading

from PyQt6.QtCore import QThread, pyqtSignal

from DrissionPage import Chromium, ChromiumOptions
from crawler import crawl_answers, _interruptible_sleep


class LogRedirector(io.TextIOBase):
    """将 write() 调用转发为 Qt 信号。"""

    def __init__(self, signal):
        super().__init__()
        self._signal = signal

    def write(self, text):
        if text and text.strip():
            self._signal.emit(text.rstrip("\n"))
        return len(text) if text else 0

    def flush(self):
        pass


class CrawlWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)       # saved, total
    finished_ok = pyqtSignal(int)          # total_saved
    error = pyqtSignal(str)
    login_needed = pyqtSignal()
    terminated = pyqtSignal()              # 用户主动结束后发射
    paused = pyqtSignal()
    resumed = pyqtSignal()

    def __init__(self, targets, output_dir, delay_range, max_answers,
                 browser_path=None, parent=None):
        super().__init__(parent)
        self.targets = targets
        self.output_dir = output_dir
        self.delay_range = delay_range
        self.max_answers = max_answers
        self.browser_path = browser_path
        self._stop_flag = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初始状态：运行中（未暂停）
        self._browser = None

    def request_stop(self):
        """终止任务（不可恢复）。"""
        self._stop_flag = True
        self._pause_event.set()  # 如果正在暂停中，先唤醒再终止

    def pause(self):
        """暂停任务（可恢复）。"""
        self._pause_event.clear()
        self.paused.emit()

    def resume(self):
        """继续任务。"""
        self._pause_event.set()
        self.resumed.emit()

    @property
    def is_paused(self):
        return not self._pause_event.is_set()

    def _is_stopped(self):
        return self._stop_flag

    # ------------------------------------------------------------------

    def run(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = LogRedirector(self.log)
        sys.stdout = redirector
        sys.stderr = redirector

        try:
            self._run_inner()
        except Exception as exc:
            if not self._stop_flag:
                self.error.emit(str(exc))
        finally:
            self._quit_browser()
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _quit_browser(self):
        if self._browser:
            try:
                self._browser.quit()
            except Exception:
                pass
            self._browser = None

    # ------------------------------------------------------------------

    def _extract_user_id(self, url: str) -> str:
        match = re.search(r'zhihu\.com/people/([^/?#]+)', url)
        if match:
            return match.group(1).rstrip('/')
        clean = url.strip().strip('/')
        if clean and not clean.startswith('http'):
            return clean
        return ''

    def _wait_for_login(self, tab, timeout=300):
        self.login_needed.emit()
        print("请在弹出的浏览器窗口中登录知乎（扫码或账号密码）")
        print(f"登录成功后会自动继续，最多等待 {timeout // 60} 分钟")

        start = time.time()
        tick = 0
        while time.time() - start < timeout:
            if self._stop_flag:
                return False
            tick += 1
            try:
                cookies = tab.cookies()
                names = [c.get('name', '') for c in cookies] if cookies else []
                if 'z_c0' in names:
                    print("登录成功！")
                    return True
                if 'signin' not in tab.url and 'sign-in' not in tab.url:
                    avatar = tab.ele('css:.AppHeader-profileEntry', timeout=2)
                    if avatar:
                        print("登录成功！")
                        return True
                if tick % 4 == 0:
                    elapsed = int(time.time() - start)
                    print(f"等待登录中... ({elapsed} 秒)")
            except Exception:
                pass
            time.sleep(3)

        print("等待登录超时")
        return False

    def _ensure_login(self, browser):
        tab = browser.latest_tab
        tab.get('https://www.zhihu.com/')
        if _interruptible_sleep(3, self._is_stopped, self._pause_event):
            return None

        logged_in = False
        try:
            cookies = tab.cookies()
            names = [c.get('name', '') for c in cookies] if cookies else []
            logged_in = 'z_c0' in names
        except Exception:
            pass

        if logged_in:
            print("已处于登录状态，无需重复登录。")
        else:
            tab.get('https://www.zhihu.com/signin')
            if _interruptible_sleep(2, self._is_stopped, self._pause_event):
                return None
            if not self._wait_for_login(tab):
                return None

        if _interruptible_sleep(2, self._is_stopped, self._pause_event):
            return None
        return tab

    # ------------------------------------------------------------------

    def _run_inner(self):
        user_ids = []
        for url in self.targets:
            uid = self._extract_user_id(url)
            if uid:
                user_ids.append(uid)

        if not user_ids:
            self.error.emit("未找到有效的目标用户，请检查输入。")
            return

        print("=" * 50)
        print(f"目标用户: {', '.join(user_ids)}")
        count_desc = '全部' if self.max_answers == 0 else f'每人最多 {self.max_answers} 条'
        print(f"爬取数量: {count_desc}")
        print(f"翻页间隔: {self.delay_range[0]}-{self.delay_range[1]} 秒")
        print(f"输出目录: {self.output_dir}")
        print("=" * 50)

        print("\n启动浏览器...")
        co = ChromiumOptions()
        co.auto_port(True)
        co.set_argument('--disable-blink-features=AutomationControlled')
        if self.browser_path:
            co.set_browser_path(self.browser_path)
        self._browser = Chromium(co)

        print("检查登录状态...")
        tab = self._ensure_login(self._browser)
        if tab is None:
            if self._stop_flag:
                print("已终止。")
                self.terminated.emit()
            else:
                self.error.emit("登录失败或超时，已停止。")
            return

        total_saved = 0
        was_terminated = False
        for i, user_id in enumerate(user_ids, 1):
            if self._stop_flag:
                was_terminated = True
                break

            print(f"\n{'#' * 50}")
            print(f"[{i}/{len(user_ids)}] 开始爬取用户: {user_id}")
            print(f"{'#' * 50}")

            user_output = os.path.join(self.output_dir, user_id)
            saved = crawl_answers(
                tab=tab,
                user_id=user_id,
                output_dir=user_output,
                max_answers=self.max_answers,
                delay_range=self.delay_range,
                stop_check=self._is_stopped,
                pause_event=self._pause_event,
            )
            total_saved += saved
            self.progress.emit(total_saved, 0)

            if self._stop_flag:
                was_terminated = True
                break

            if i < len(user_ids):
                print("切换用户前等待 10 秒...")
                if _interruptible_sleep(10, self._is_stopped, self._pause_event):
                    was_terminated = True
                    break

        if was_terminated:
            print(f"\n已终止。本次共保存 {total_saved} 条回答。")
            self.terminated.emit()
        else:
            print(f"\n{'=' * 50}")
            print(f"全部完成！共爬取 {len(user_ids)} 个用户，保存 {total_saved} 条回答")
            print(f"输出目录: {self.output_dir}")
            print("=" * 50)
            self.finished_ok.emit(total_saved)
