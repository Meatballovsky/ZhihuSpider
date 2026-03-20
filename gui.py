"""ZhihuSpider - PyQt6 GUI（苹果风格）"""
import json
import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox,
    QTextEdit, QVBoxLayout, QWidget, QLineEdit, QGroupBox, QFormLayout,
)

from browser_finder import find_browser
from worker import CrawlWorker
from main import __version__ as VERSION

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
ICON_PATH = os.path.join(RESOURCE_DIR, 'icon.ico')
ICON_PNG_PATH = os.path.join(RESOURCE_DIR, 'icon.png')

DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.expanduser("~"), "Desktop", "知乎导出"
)

ALL_CONTENT_TYPES = ['answers', 'articles', 'pins']

DEFAULT_CONTENT_SETTINGS = {
    "answers":  {"enabled": True, "max": 0},
    "articles": {"enabled": True, "max": 0},
    "pins":     {"enabled": True, "max": 0},
}

DEFAULT_CONFIG = {
    "targets": [],
    "output_dir": DEFAULT_OUTPUT_DIR,
    "page_delay_min": 8,
    "page_delay_max": 15,
    "content_settings": dict(DEFAULT_CONTENT_SETTINGS),
}

STYLESHEET = """
QMainWindow {
    background-color: #f5f5f7;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    margin-top: 8px;
    padding: 16px 12px 12px 12px;
    font-size: 13px;
    font-weight: 600;
    color: #1d1d1f;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 16px;
    color: #1d1d1f;
}

QLabel {
    color: #1d1d1f;
    font-size: 13px;
}
QLabel#hintLabel {
    color: #86868b;
    font-size: 12px;
}

QLineEdit, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    color: #1d1d1f;
    selection-background-color: #0071e3;
}
QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #0071e3;
}

QSpinBox {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 4px 8px 4px 10px;
    font-size: 13px;
    color: #1d1d1f;
    min-width: 80px;
}
QSpinBox:focus {
    border: 2px solid #0071e3;
}
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    border-left: 1px solid #e0e0e0;
    border-top-right-radius: 8px;
    background-color: #f5f5f7;
}
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    border: none;
    border-left: 1px solid #e0e0e0;
    border-top: 1px solid #e0e0e0;
    border-bottom-right-radius: 8px;
    background-color: #f5f5f7;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #e0e0e0;
}
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
    background-color: #d1d1d6;
}
QSpinBox::up-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 6px solid #1d1d1f;
    width: 0; height: 0;
}
QSpinBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #1d1d1f;
    width: 0; height: 0;
}
QSpinBox::up-arrow:disabled, QSpinBox::down-arrow:disabled {
    border-bottom-color: #aeaeb2;
    border-top-color: #aeaeb2;
}

QCheckBox {
    font-size: 13px;
    color: #1d1d1f;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #d2d2d7;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #0071e3;
    border-color: #0071e3;
}
QCheckBox::indicator:disabled {
    background-color: #e8e8ed;
    border-color: #d2d2d7;
}
QCheckBox::indicator:checked:disabled {
    background-color: #99c4f3;
    border-color: #99c4f3;
}
QCheckBox:disabled {
    color: #aeaeb2;
}

QPushButton {
    border: none;
    border-radius: 10px;
    padding: 8px 24px;
    font-size: 13px;
    font-weight: 500;
    color: #1d1d1f;
    background-color: #e8e8ed;
}
QPushButton:hover {
    background-color: #d1d1d6;
}
QPushButton:pressed {
    background-color: #c7c7cc;
}
QPushButton:disabled {
    background-color: #f2f2f7;
    color: #aeaeb2;
}

QPushButton#startBtn {
    background-color: #0071e3;
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#startBtn:hover {
    background-color: #0077ed;
}
QPushButton#startBtn:pressed {
    background-color: #006edb;
}
QPushButton#startBtn:disabled {
    background-color: #99c4f3;
    color: #ffffff;
}

QPushButton#pauseBtn {
    background-color: #ff9500;
    color: #ffffff;
    font-weight: 600;
    font-size: 13px;
}
QPushButton#pauseBtn:hover {
    background-color: #ffa726;
}
QPushButton#pauseBtn:pressed {
    background-color: #e68900;
}
QPushButton#pauseBtn:disabled {
    background-color: #f2f2f7;
    color: #aeaeb2;
}

QPushButton#endBtn {
    background-color: #ff3b30;
    color: #ffffff;
    font-weight: 600;
    font-size: 13px;
}
QPushButton#endBtn:hover {
    background-color: #ff453a;
}
QPushButton#endBtn:pressed {
    background-color: #d70015;
}
QPushButton#endBtn:disabled {
    background-color: #f2f2f7;
    color: #aeaeb2;
}

QPushButton#browseBtn {
    padding: 6px 14px;
    font-size: 12px;
    border-radius: 8px;
}

QTextEdit#logArea {
    background-color: #1d1d1f;
    color: #f5f5f7;
    border: 1px solid #3a3a3c;
    border-radius: 10px;
    padding: 10px;
    font-family: 'Cascadia Code', 'Consolas', 'Menlo', monospace;
    font-size: 12px;
    selection-background-color: #0071e3;
}

QStatusBar {
    background-color: #f5f5f7;
    color: #86868b;
    font-size: 12px;
    border-top: 1px solid #e0e0e0;
}

QFrame#typeCard {
    background-color: #f5f5f7;
    border-radius: 10px;
    padding: 8px 14px;
}

/* 全局无背景透明滚动条 */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.25);
    min-height: 30px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.4);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: rgba(0, 0, 0, 0.25);
    min-width: 30px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(0, 0, 0, 0.4);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    width: 0;
}

/* 日志区深色背景下的浅色滚动条 */
QTextEdit#logArea QScrollBar:vertical {
    background: transparent;
    width: 6px;
}
QTextEdit#logArea QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 3px;
}
QTextEdit#logArea QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.5);
}

QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
"""


def _load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def _save_config(cfg: dict):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _get_icon() -> QIcon:
    for p in (ICON_PATH, ICON_PNG_PATH):
        if os.path.exists(p):
            return QIcon(p)
    return QIcon()


class MainWindow(QMainWindow):

    STATE_IDLE = "idle"
    STATE_RUNNING = "running"
    STATE_PAUSED = "paused"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ZhihuSpider v{VERSION} - 知乎内容导出工具")
        self.setWindowIcon(_get_icon())
        self.setMinimumSize(780, 780)
        self.resize(780, 860)
        self.worker = None
        self.browser_path = None
        self.browser_name = ""
        self._btn_state = self.STATE_IDLE

        self._build_ui()
        self._load_defaults()
        self._detect_browser()

    # ---- UI ----

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        root = QVBoxLayout(scroll_content)
        root.setSpacing(12)
        root.setContentsMargins(20, 20, 20, 12)
        scroll.setWidget(scroll_content)
        outer.addWidget(scroll, stretch=1)

        # --- 标题 ---
        title = QLabel("知乎内容导出")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1d1d1f; margin-bottom: 4px;")
        root.addWidget(title)

        subtitle = QLabel("输入知乎用户主页，一键提取回答、文章、想法")
        subtitle.setObjectName("hintLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)

        # --- 输入区 ---
        grp_input = QGroupBox("目标用户")
        lay_input = QVBoxLayout(grp_input)
        lay_input.setSpacing(6)
        hint = QLabel("每行一个知乎用户主页 URL，例如：\n"
                       "https://www.zhihu.com/people/xubinlvshi/answers")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        lay_input.addWidget(hint)
        self.txt_targets = QTextEdit()
        self.txt_targets.setMaximumHeight(90)
        self.txt_targets.setPlaceholderText("粘贴 URL，每行一个...")
        lay_input.addWidget(self.txt_targets)
        root.addWidget(grp_input)

        # --- 设置区 ---
        grp_settings = QGroupBox("设置")
        form = QFormLayout(grp_settings)
        form.setSpacing(10)
        form.setContentsMargins(12, 20, 12, 12)

        row_dir = QHBoxLayout()
        self.txt_output = QLineEdit()
        self.txt_output.setPlaceholderText("选择输出目录...")
        btn_browse = QPushButton("浏览...")
        btn_browse.setObjectName("browseBtn")
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_output)
        row_dir.addWidget(self.txt_output)
        row_dir.addWidget(btn_browse)
        form.addRow("输出目录：", row_dir)

        row_delay = QHBoxLayout()
        self.spn_delay_min = QSpinBox()
        self.spn_delay_min.setRange(1, 120)
        self.spn_delay_min.setSuffix(" 秒")
        row_delay.addWidget(self.spn_delay_min)
        lbl_sep = QLabel("~")
        lbl_sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sep.setFixedWidth(20)
        row_delay.addWidget(lbl_sep)
        self.spn_delay_max = QSpinBox()
        self.spn_delay_max.setRange(1, 120)
        self.spn_delay_max.setSuffix(" 秒")
        row_delay.addWidget(self.spn_delay_max)
        row_delay.addStretch()
        form.addRow("翻页间隔：", row_delay)

        root.addWidget(grp_settings)

        # --- 提取内容区（卡片式） ---
        grp_content = QGroupBox("提取内容")
        lay_content = QVBoxLayout(grp_content)
        lay_content.setSpacing(8)
        lay_content.setContentsMargins(12, 20, 12, 12)

        self._type_cards = {}
        for key, label in [('answers', '回答'), ('articles', '文章'), ('pins', '想法')]:
            card, widgets = self._build_type_card(key, label)
            lay_content.addWidget(card)
            self._type_cards[key] = widgets

        root.addWidget(grp_content)

        # --- 按钮区：开始 | 暂停/继续 | 结束 ---
        row_btn = QHBoxLayout()
        row_btn.setSpacing(12)

        self.btn_start = QPushButton("开始提取")
        self.btn_start.setObjectName("startBtn")
        self.btn_start.setFixedHeight(42)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._on_start)
        row_btn.addWidget(self.btn_start, stretch=2)

        self.btn_pause = QPushButton("暂停")
        self.btn_pause.setObjectName("pauseBtn")
        self.btn_pause.setFixedHeight(42)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause.clicked.connect(self._on_pause_toggle)
        row_btn.addWidget(self.btn_pause, stretch=1)

        self.btn_end = QPushButton("结束")
        self.btn_end.setObjectName("endBtn")
        self.btn_end.setFixedHeight(42)
        self.btn_end.setEnabled(False)
        self.btn_end.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_end.clicked.connect(self._on_end)
        row_btn.addWidget(self.btn_end, stretch=1)

        root.addLayout(row_btn)

        # --- 日志区 ---
        grp_log = QGroupBox("运行日志")
        lay_log = QVBoxLayout(grp_log)
        lay_log.setContentsMargins(8, 20, 8, 8)
        self.txt_log = QTextEdit()
        self.txt_log.setObjectName("logArea")
        self.txt_log.setReadOnly(True)
        self.txt_log.setMinimumHeight(200)
        lay_log.addWidget(self.txt_log)
        root.addWidget(grp_log, stretch=1)

        # --- 状态栏 ---
        self.statusBar().showMessage("就绪")

    # ---- 卡片构建 ----

    def _build_type_card(self, key: str, label: str):
        """构建单个内容类型卡片，返回 (card_widget, widgets_dict)。"""
        card = QFrame()
        card.setObjectName("typeCard")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        chk_enable = QCheckBox(label)
        chk_enable.setChecked(True)
        chk_enable_font = chk_enable.font()
        chk_enable_font.setBold(True)
        chk_enable.setFont(chk_enable_font)
        lay.addWidget(chk_enable)

        sep = QLabel("|")
        sep.setFixedWidth(10)
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setStyleSheet("color: #d2d2d7;")
        lay.addWidget(sep)

        chk_all = QCheckBox("提取全部")
        chk_all.setChecked(True)
        lay.addWidget(chk_all)

        spn = QSpinBox()
        spn.setRange(1, 99999)
        spn.setValue(100)
        spn.setSuffix(" 条")
        spn.setEnabled(False)
        spn.setFixedWidth(100)
        lay.addWidget(spn)

        lay.addStretch()

        def _on_enable_toggled(checked, _chk_all=chk_all, _spn=spn):
            _chk_all.setEnabled(checked)
            _spn.setEnabled(checked and not _chk_all.isChecked())

        def _on_all_toggled(checked, _chk_enable=chk_enable, _spn=spn):
            _spn.setEnabled(_chk_enable.isChecked() and not checked)

        chk_enable.toggled.connect(_on_enable_toggled)
        chk_all.toggled.connect(_on_all_toggled)

        widgets = {
            'chk_enable': chk_enable,
            'chk_all': chk_all,
            'spn_max': spn,
        }
        return card, widgets

    # ---- 按钮状态机 ----

    def _set_btn_state(self, state: str):
        self._btn_state = state
        is_idle = state == self.STATE_IDLE
        is_running = state == self.STATE_RUNNING
        is_paused = state == self.STATE_PAUSED

        self.btn_start.setEnabled(is_idle)
        self.btn_pause.setEnabled(is_running or is_paused)
        self.btn_end.setEnabled(is_running or is_paused)

        if is_paused:
            self.btn_pause.setText("继续")
            self.btn_pause.setStyleSheet(
                "QPushButton { background-color: #34c759; color: #fff; "
                "font-weight: 600; border: none; border-radius: 10px; }"
                "QPushButton:hover { background-color: #30d158; }"
                "QPushButton:pressed { background-color: #28a745; }"
            )
        else:
            self.btn_pause.setText("暂停")
            self.btn_pause.setStyleSheet("")

        inputs_locked = not is_idle
        self.txt_targets.setReadOnly(inputs_locked)
        self.txt_output.setReadOnly(inputs_locked)
        self.spn_delay_min.setReadOnly(inputs_locked)
        self.spn_delay_max.setReadOnly(inputs_locked)
        for w in self._type_cards.values():
            w['chk_enable'].setEnabled(is_idle)
            w['chk_all'].setEnabled(is_idle and w['chk_enable'].isChecked())
            w['spn_max'].setEnabled(
                is_idle and w['chk_enable'].isChecked() and not w['chk_all'].isChecked()
            )

    # ---- 内容类型设置 ----

    def _get_content_limits(self) -> dict:
        """返回启用类型及其数量限制，如 {'answers': 0, 'articles': 50}，0 表示全部。"""
        limits = {}
        for key, w in self._type_cards.items():
            if w['chk_enable'].isChecked():
                limits[key] = 0 if w['chk_all'].isChecked() else w['spn_max'].value()
        return limits

    # ---- 配置读写 ----

    def _load_defaults(self):
        cfg = _load_config()
        targets = cfg.get('targets', [])
        if targets:
            self.txt_targets.setPlainText('\n'.join(targets))

        out = cfg.get('output_dir', DEFAULT_OUTPUT_DIR)
        if not os.path.isabs(out):
            out = os.path.normpath(os.path.join(BASE_DIR, out))
        self.txt_output.setText(out)

        self.spn_delay_min.setValue(cfg.get('page_delay_min', 8))
        self.spn_delay_max.setValue(cfg.get('page_delay_max', 15))

        cs = cfg.get('content_settings', DEFAULT_CONTENT_SETTINGS)
        for key, w in self._type_cards.items():
            s = cs.get(key, {'enabled': True, 'max': 0})
            w['chk_enable'].setChecked(s.get('enabled', True))
            max_val = s.get('max', 0)
            if max_val == 0:
                w['chk_all'].setChecked(True)
                w['spn_max'].setValue(100)
            else:
                w['chk_all'].setChecked(False)
                w['spn_max'].setValue(max_val)

    def _save_current_config(self):
        lines = self.txt_targets.toPlainText().strip().splitlines()
        targets = [l.strip() for l in lines if l.strip()]
        out_dir = self.txt_output.text().strip()
        cs = {}
        for key, w in self._type_cards.items():
            cs[key] = {
                'enabled': w['chk_enable'].isChecked(),
                'max': 0 if w['chk_all'].isChecked() else w['spn_max'].value(),
            }
        cfg = {
            "targets": targets,
            "output_dir": out_dir.replace('\\', '/'),
            "page_delay_min": self.spn_delay_min.value(),
            "page_delay_max": self.spn_delay_max.value(),
            "content_settings": cs,
        }
        _save_config(cfg)

    # ---- 浏览器检测 ----

    def _detect_browser(self):
        path, name = find_browser()
        if path:
            self.browser_path = path
            self.browser_name = name
            self.statusBar().showMessage(f"已检测到浏览器: {name}  ({path})")
            self._append_log(f"[浏览器] 已检测到 {name}: {path}")
        else:
            self._append_log("[浏览器] 未自动检测到 Chromium 内核浏览器，请手动选择...")
            path, _ = QFileDialog.getOpenFileName(
                self, "选择 Chromium 内核浏览器",
                "C:\\Program Files",
                "可执行文件 (*.exe)",
            )
            if path:
                self.browser_path = path
                self.browser_name = os.path.basename(path)
                self.statusBar().showMessage(f"浏览器: {self.browser_name}  ({path})")
                self._append_log(f"[浏览器] 用户选择: {path}")
            else:
                self.browser_path = None
                self.statusBar().showMessage("未指定浏览器，无法运行")
                self.btn_start.setEnabled(False)
                self._append_log("[浏览器] 未选择浏览器，开始按钮已禁用")

    # ---- 按钮回调 ----

    def _on_start(self):
        lines = self.txt_targets.toPlainText().strip().splitlines()
        targets = [l.strip() for l in lines if l.strip()]
        if not targets:
            QMessageBox.warning(self, "提示", "请输入至少一个目标 URL")
            return

        content_limits = self._get_content_limits()
        if not content_limits:
            QMessageBox.warning(self, "提示", "请至少勾选一种内容类型")
            return

        output_dir = self.txt_output.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "提示", "请指定输出目录")
            return

        os.makedirs(output_dir, exist_ok=True)
        self._save_current_config()

        delay_min = self.spn_delay_min.value()
        delay_max = self.spn_delay_max.value()
        if delay_min > delay_max:
            delay_min, delay_max = delay_max, delay_min

        self.txt_log.clear()
        self._set_btn_state(self.STATE_RUNNING)
        self.statusBar().showMessage("运行中...")

        self.worker = CrawlWorker(
            targets=targets,
            output_dir=output_dir,
            delay_range=(delay_min, delay_max),
            content_limits=content_limits,
            browser_path=self.browser_path,
        )
        self.worker.log.connect(self._append_log)
        self.worker.error.connect(self._on_error)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.terminated.connect(self._on_terminated)
        self.worker.login_needed.connect(self._on_login_needed)
        self.worker.paused.connect(lambda: self.statusBar().showMessage("已暂停"))
        self.worker.resumed.connect(lambda: self.statusBar().showMessage("运行中..."))
        self.worker.finished.connect(self._on_thread_done)
        self.worker.start()

    def _on_pause_toggle(self):
        if not self.worker or not self.worker.isRunning():
            return
        if self.worker.is_paused:
            self.worker.resume()
            self._set_btn_state(self.STATE_RUNNING)
            self._append_log("[用户] 已继续")
            self.statusBar().showMessage("运行中...")
        else:
            self.worker.pause()
            self._set_btn_state(self.STATE_PAUSED)
            self._append_log("[用户] 已暂停，点击「继续」可恢复")
            self.statusBar().showMessage("已暂停")

    def _on_end(self):
        if not self.worker or not self.worker.isRunning():
            return
        reply = QMessageBox.question(
            self, "确认结束",
            "确定要结束任务吗？\n将终止爬取并关闭浏览器，已保存的数据不受影响。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return
        self.btn_pause.setEnabled(False)
        self.btn_end.setEnabled(False)
        self.btn_end.setText("正在结束...")
        self._append_log("[用户] 正在结束任务...")
        self.statusBar().showMessage("正在结束...")
        self.worker.request_stop()

    # ---- 信号处理 ----

    def _append_log(self, text: str):
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)
        self.txt_log.insertPlainText(text + "\n")
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)

    def _on_error(self, msg: str):
        self._append_log(f"[错误] {msg}")
        QMessageBox.critical(self, "错误", msg)

    def _on_login_needed(self):
        self._append_log("[提示] 请在弹出的浏览器中登录知乎...")
        self.statusBar().showMessage("等待登录...")

    def _on_finished(self, total: int):
        self._append_log(f"\n完成！共保存 {total} 条内容。")
        self.statusBar().showMessage(f"完成 - 共 {total} 条")

    def _on_terminated(self):
        self.statusBar().showMessage("已结束")

    def _on_thread_done(self):
        self._set_btn_state(self.STATE_IDLE)
        self.btn_end.setText("结束")
        msg = self.statusBar().currentMessage()
        if not msg or msg in ("运行中...", "等待登录...", "正在结束..."):
            self.statusBar().showMessage("就绪")

    # ---- 其他 ----

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.txt_output.text())
        if path:
            self.txt_output.setText(path)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "爬虫正在运行，确定要退出吗？\n（将终止任务并关闭浏览器）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.worker.request_stop()
            self.worker.wait(5000)
        self._save_current_config()
        event.accept()


def run_gui():
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'zhihu.spider.gui.1.0'
        )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    app.setWindowIcon(_get_icon())

    font = QFont("Microsoft YaHei UI", 9)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_gui()
