<div align="center">

<img src="icon.svg" width="80" height="80" alt="ZhihuSpider Logo">

# ZhihuSpider

**一键导出知乎用户的回答、文章、想法，保存为 Markdown 文件**

知乎不提供"导出我的内容"功能。这个工具帮你拿回属于你的内容。

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![Release](https://img.shields.io/github/v/release/lemoabc/ZhihuSpider?color=orange)](https://github.com/lemoabc/ZhihuSpider/releases)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)](https://github.com)

[快速开始](#-快速开始) · [GUI 模式](#-gui-模式) · [CLI 模式](#-cli-模式) · [更新日志](#-更新日志) · [常见问题](#-faq)

</div>

---

## 📋 更新日志

### v1.1.0 — 多内容类型支持 `2026-03-20`

> 从"回答导出工具"进化为"知乎内容全量导出工具"

- **新增** 支持导出**文章**和**想法**，不再局限于回答
- **新增** 每种内容类型独立设置下载数量（卡片式 UI）
- **新增** 内容按类型分目录存储：`输出目录/用户ID/回答/`、`文章/`、`想法/`
- **优化** 窗口可滚动、透明滚动条、日志区增大
- **优化** 内容类型取消勾选时子控件正确灰显禁用
- **修复** DrissionPage `listen.wait()` 超时返回值兼容

### v1.0.1 — Bug 修复 `2026-03-17`

- **修复** 打包 EXE 后任务栏图标不显示的问题

### v1.0.0 — 首个公开版本 `2026-03-15`

- GUI + CLI 双模式
- 基于 DrissionPage 真实浏览器驱动
- 拟人化翻页策略（随机延迟 + 随机滚动）
- 自动检测本地 Chromium 浏览器
- 暂停 / 继续 / 终止控制
- Markdown 格式输出，图片链接完整保留
- 多用户批量爬取
- PyInstaller 一键打包 EXE

---

## 为什么需要这个工具？

- 知乎没有官方的"导出内容"功能
- 你辛辛苦苦写的回答、文章、想法，只能在知乎平台上看
- 万一哪天账号出问题，多年心血付之东流
- 想把内容搬到公众号、博客、本地归档？只能一篇篇手动复制

**ZhihuSpider 解决这些问题**：输入用户主页链接，自动爬取回答、文章、想法，每条内容保存为一个格式优美的 Markdown 文件。

## 亮点

- **三种内容全支持**：回答、文章、想法一键导出，独立控制数量
- **双模式**：GUI 图形界面（小白友好）+ CLI 命令行（极客最爱）
- **真实浏览器**：基于 DrissionPage 驱动真实浏览器，行为与人工浏览一致
- **拟人化策略**：随机延迟 + 随机滚动距离 + 抖动间隔，极大降低风控风险
- **智能浏览器检测**：自动查找 Chrome / Edge / 360 / QQ浏览器，无需手动配置
- **暂停 & 继续**：长时间爬取中途可暂停，喝杯咖啡回来继续
- **Markdown 输出**：图片链接、加粗、引用等格式完整保留
- **分目录存储**：按用户 → 内容类型自动整理到子文件夹
- **多用户批量**：一次配置多个用户，登录一次，依次爬取
- **可打包 EXE**：一键打包成独立可执行文件，分发无忧

## 效果预览

**GUI 模式**

```
┌─────────────────────────────────────────┐
│  🔗 目标URL: zhihu.com/people/xxx      │
│  📁 输出到:  ~/Desktop/知乎导出         │
│  ⏱  间隔:   8~15 秒                    │
│                                         │
│  ┌──────────┐┌──────────┐┌──────────┐  │
│  │☑ 回答    ││☑ 文章    ││☑ 想法    │  │
│  │☑ 提取全部││  50 条   ││☑ 提取全部│  │
│  └──────────┘└──────────┘└──────────┘  │
│                                         │
│  [ 开始提取 ]  [ 暂停 ]  [ 结束 ]       │
│                                         │
│  ✅ [第3页] 已保存 60/4637 条回答        │
│  ⏳ 休息 12 秒...                       │
└─────────────────────────────────────────┘
```

**输出目录结构**

```
知乎导出/
└── xubinlvshi/
    ├── 回答/
    │   ├── 如何评价某某事件-1234赞.md
    │   └── ...
    ├── 文章/
    │   ├── 房产律师教你看合同-567赞.md
    │   └── ...
    └── 想法/
        ├── 2026-03-18-经过150天的努力.md
        └── ...
```

**输出的 Markdown 文件**

```markdown
# [如何评价某某事件？](https://www.zhihu.com/question/xxx/answer/xxx)

**作者名** / 2026-03-09 👍 1234

---

回答正文内容，包含 **加粗**、*斜体*、
![图片](https://pic.zhimg.com/xxx.jpg) 和 [链接](url) ...
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/lemoabc/ZhihuSpider.git
cd ZhihuSpider
```

### 2. 安装依赖

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 运行

```bash
python main.py
```

弹出 GUI 界面，输入目标用户的知乎主页链接，点击"开始提取"即可。

首次运行需要在弹出的浏览器窗口中扫码登录知乎（仅需一次）。

> 也可以直接下载 [Releases](https://github.com/lemoabc/ZhihuSpider/releases) 中的 EXE 文件，双击即用，无需安装 Python。

## 🖥 GUI 模式

直接运行 `python main.py`（默认）：

1. 填写目标用户的知乎主页 URL
2. 设置输出目录和爬取参数
3. 勾选要导出的内容类型（回答 / 文章 / 想法），分别设置数量
4. 点击 **开始提取**
5. 在弹出的浏览器中登录知乎
6. 坐等完成

**按钮说明**：
- **暂停 / 继续**：暂停当前爬取，再次点击恢复
- **结束**：立即终止爬取并关闭浏览器

## ⌨ CLI 模式

```bash
python main.py --cli
```

首次运行会自动生成 `config.json`，编辑后重新运行：

```json
{
  "targets": [
    "https://www.zhihu.com/people/目标用户ID/answers"
  ],
  "output_dir": "./output",
  "page_delay_min": 8,
  "page_delay_max": 15,
  "content_settings": {
    "answers":  { "enabled": true, "max": 0 },
    "articles": { "enabled": true, "max": 0 },
    "pins":     { "enabled": true, "max": 0 }
  }
}
```

> `max` 设为 `0` 表示全部导出；设为 `false` 的 `enabled` 表示跳过该类型。

### 多用户批量爬取

```json
{
  "targets": [
    "https://www.zhihu.com/people/user1/answers",
    "https://www.zhihu.com/people/user2/answers",
    "user3"
  ]
}
```

只需登录一次，程序会依次爬取每个用户，输出到各自的子文件夹。

## 📦 打包为 EXE

```bash
# Windows
.\build.bat
```

生成的 `dist/ZhihuSpider.exe` 可以直接分发，双击运行。

## 📁 项目结构

```
ZhihuSpider/
├── main.py              # 入口（GUI / CLI 双模式）
├── gui.py               # PyQt6 图形界面
├── crawler.py           # 爬虫核心逻辑（回答 / 文章 / 想法）
├── converter.py         # HTML → Markdown 转换 & 文件保存
├── worker.py            # 异步工作线程
├── browser_finder.py    # 自动检测本地浏览器
├── build.bat            # Windows 一键打包脚本
├── config.example.json  # 配置文件模板
├── requirements.txt     # Python 依赖
├── icon.svg / ico / png # 应用图标
└── LICENSE              # MIT 开源协议
```

## ⚙ 配置说明

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `targets` | 目标用户 URL 列表 | — |
| `output_dir` | 输出目录 | `./output` |
| `content_settings` | 各内容类型的启用与数量设置 | 全部启用，全量导出 |
| `page_delay_min` | 翻页最小间隔（秒） | `8` |
| `page_delay_max` | 翻页最大间隔（秒） | `15` |

`targets` 支持多种写法：

```
https://www.zhihu.com/people/用户ID/answers  ✅ 完整链接
https://www.zhihu.com/people/用户ID          ✅ 不带 /answers 也行
用户ID                                       ✅ 直接写 ID
```

`content_settings` 各类型配置：

| 类型 | 键名 | 说明 |
|------|------|------|
| 回答 | `answers` | 用户的知乎回答 |
| 文章 | `articles` | 用户发表的专栏文章 |
| 想法 | `pins` | 用户发布的想法（类似微博） |

每个类型支持 `enabled`（是否启用）和 `max`（最大条数，`0` = 全部）。

## ❓ FAQ

<details>
<summary><b>会不会封号？</b></summary>

风险极低。程序通过真实浏览器操作，行为与手动翻看页面一致。默认 8-15 秒翻一页，加上随机延迟和随机滚动，比正常人浏览还慢。最坏情况是弹出验证码或临时限制访问，不会直接封号。
</details>

<details>
<summary><b>支持哪些浏览器？</b></summary>

自动检测顺序：Chrome → Edge → 360安全浏览器 → QQ浏览器。找不到时会弹窗让你手动选择浏览器路径。只要是 Chromium 内核的浏览器都支持。
</details>

<details>
<summary><b>能不能只导出部分内容？</b></summary>

可以。在 GUI 中取消勾选不需要的内容类型，或取消"提取全部"并输入具体数量。CLI 模式下在 `content_settings` 中设置 `enabled: false` 或指定 `max` 数值。
</details>

<details>
<summary><b>中途中断了怎么办？</b></summary>

已保存的文件不会丢失。重新运行会从头开始爬取（同名文件会被覆盖）。
</details>

<details>
<summary><b>macOS / Linux 能用吗？</b></summary>

核心爬虫逻辑跨平台，GUI 基于 PyQt6 也跨平台。浏览器检测目前针对 Windows 优化，其他系统需要确保 Chrome 或 Chromium 在 PATH 中即可。EXE 打包仅限 Windows。
</details>

## 🤝 贡献

欢迎提 Issue 和 PR！以下是一些可能的方向：

- [ ] 断点续爬（跳过已保存的内容）
- [ ] 导出为其他格式（PDF、HTML、EPUB）
- [ ] macOS / Linux 浏览器自动检测
- [ ] 国际化（i18n）

## 📜 许可证

[MIT License](LICENSE) — 随便用，标注来源即可。

## Star History

如果这个项目帮到了你，请点个 ⭐ 让更多人看到！

---

<div align="center">

**用 ZhihuSpider 拿回属于你的内容。**

</div>
