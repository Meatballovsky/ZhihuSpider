<div align="center">

<img src="icon.svg" width="80" height="80" alt="ZhihuSpider Logo">

# ZhihuSpider

**一键导出知乎用户的全部回答，保存为 Markdown 文件**

知乎不提供"导出我的回答"功能。这个工具帮你拿回属于你的内容。

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)](https://github.com)

[快速开始](#-快速开始) · [GUI 模式](#-gui-模式) · [CLI 模式](#-cli-模式) · [常见问题](#-faq)

</div>

---

## 为什么需要这个工具？

- 知乎没有官方的"导出回答"功能
- 你辛辛苦苦写的几百上千条回答，只能在知乎平台上看
- 万一哪天账号出问题，多年心血付之东流
- 想把内容搬到公众号、博客、本地归档？只能一篇篇手动复制

**ZhihuSpider 解决这些问题**：输入用户主页链接，自动爬取全部回答，每条回答保存为一个格式优美的 Markdown 文件。

## 亮点

- **双模式**：GUI 图形界面（小白友好）+ CLI 命令行（极客最爱）
- **真实浏览器**：基于 DrissionPage 驱动真实浏览器，行为与人工浏览一致
- **拟人化策略**：随机延迟 + 随机滚动距离 + 抖动间隔，极大降低风控风险
- **智能浏览器检测**：自动查找 Chrome / Edge / 360 / QQ浏览器，无需手动配置
- **暂停 & 继续**：长时间爬取中途可暂停，喝杯咖啡回来继续
- **Markdown 输出**：图片链接、加粗、引用等格式完整保留
- **多用户批量**：一次配置多个用户，登录一次，依次爬取
- **可打包 EXE**：一键打包成独立可执行文件，分发无忧

## 效果预览

**GUI 模式**

```
┌─────────────────────────────────────────┐
│  🔗 目标URL: zhihu.com/people/xxx      │
│  📁 输出到:  ~/Desktop/知乎回答         │
│  ⏱  间隔:   8~15 秒                    │
│                                         │
│  [ 开始提取 ]  [ 暂停 ]  [ 结束 ]       │
│                                         │
│  ✅ [第3页] 已保存 60/4637 条            │
│  ⏳ 休息 12 秒...                       │
└─────────────────────────────────────────┘
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

## 🖥 GUI 模式

直接运行 `python main.py`（默认）：

1. 填写目标用户的知乎回答页 URL
2. 设置输出目录和爬取参数
3. 点击 **开始提取**
4. 在弹出的浏览器中登录知乎
5. 坐等完成

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
  "max_answers": 0
}
```

> `max_answers` 设为 `0` 表示爬取全部回答。

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
├── crawler.py           # 爬虫核心逻辑
├── converter.py         # HTML → Markdown 转换
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
| `max_answers` | 最多爬取条数，`0` = 全部 | `0` |
| `page_delay_min` | 翻页最小间隔（秒） | `8` |
| `page_delay_max` | 翻页最大间隔（秒） | `15` |

`targets` 支持多种写法：

```
https://www.zhihu.com/people/用户ID/answers  ✅ 完整链接
https://www.zhihu.com/people/用户ID          ✅ 不带 /answers 也行
用户ID                                       ✅ 直接写 ID
```

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
<summary><b>能不能只爬某个用户的部分回答？</b></summary>

在 GUI 中取消勾选"提取全部"，输入想要的数量；CLI 模式下设置 `max_answers` 为具体数字即可。
</details>

<details>
<summary><b>中途中断了怎么办？</b></summary>

已保存的文件不会丢失。重新运行会从头开始爬取（同名文件会被覆盖）。
</details>

<details>
<summary><b>能爬取知乎文章或想法吗？</b></summary>

目前只支持"回答"。文章和想法的支持在计划中，欢迎提 Issue 或 PR。
</details>

<details>
<summary><b>macOS / Linux 能用吗？</b></summary>

核心爬虫逻辑跨平台，GUI 基于 PyQt6 也跨平台。浏览器检测目前针对 Windows 优化，其他系统需要确保 Chrome 或 Chromium 在 PATH 中即可。EXE 打包仅限 Windows。
</details>

## 🤝 贡献

欢迎提 Issue 和 PR！尤其欢迎以下方向的贡献：

- [ ] 支持爬取知乎文章（Articles）
- [ ] 支持爬取知乎想法（Pins）
- [ ] 断点续爬（跳过已保存的回答）
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
