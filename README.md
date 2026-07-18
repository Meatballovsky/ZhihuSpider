# ZhihuBackup Crawler

知乎用户 ****（""）的回答与文章增量爬取工具。

## 为什么做这个

在知乎写的内容分散在平台上——随时可能被删、被限流、或被算法埋没。
增量爬取确保任何 agent 可以在本地重建完整知识库，无需依赖知乎。

## ⚠️ 前置条件（必须遵守）

在运行爬虫前，必须先启动 Edge 浏览器实例：

```bash
# 1. 启动隔离版 Edge（启用 CDP 端口 9222）
~/agent_projects/agent_edge_launcher/launch_agent_edge.sh
```

这会在端口 9222 启动一个独立配置文件（`Agent Profile`）的 Edge，Cookie 注入和爬取都连接到此实例。

## Cookie 管理

### 首次使用：提取 Cookie

如果 Edge Agent Profile 已登录知乎，直接导出 Cookie：

```bash
source venv/bin/activate
python cookie_injector.py --export-cookies /tmp/zhihu-scraper/.local/cookies.json
```

这会从 Edge 提取所有 `.zhihu.com` 的 Cookie，保存到 JSON 文件。

### 如果已导出 Cookie

直接 Inject Cookie：

```bash
python cookie_injector.py
```

## 完整操作流程

### 首次爬取（完整流程）

```bash
# 1. 启动 Edge Agent Profile
~/agent_projects/agent_edge_launcher/launch_agent_edge.sh

# 2. 在 Edge 中登录知乎（首次需要）

# 3. 导出 Cookie 到本地文件
source venv/bin/activate
python cookie_injector.py --export-cookies /tmp/zhihu-scraper/.local/cookies.json

# 4. 运行爬取（cookie 会自动注入）
python run.py
```

### 后续增量爬取

```bash
# 1. 启动 Edge
~/agent_projects/agent_edge_launcher/launch_agent_edge.sh

# 2. 爬取（Cookie 已保存在本地，自动注入）
python run.py --only-articles
```

### 跳过 Cookie 注入（Edge 已登录知乎）

```bash
python run.py --no-cookie-inject
```

## Cookie 注入原理

```
[Edge Agent Profile]
    │
    │ CDP (Chrome DevTools Protocol) on port 9222
    │
[cookie_injector.py]
    │ Reads JSON from /tmp/zhihu-scraper/.local/cookies.json
    │ Sends Network.setCookie commands via HTTP CDP
    │
[Edge Browser]
    │ Cookie DB (SQLite)
    │ 
[https://www.zhihu.com]
    │ Cookie accepted → User logged in
    │
[crawler.py]
    │ Navigates to 's profile
    │ Extracts answer/article cards
    │ Saves as Markdown
```

## 快速开始

### 查看爬取进度

```bash
python -c "import json; d=json.load(open('.index_回答.json')); print(f'已爬: {len(d)} 条')"
python -c "import json; d=json.load(open('.index_文章.json')); print(f'已爬: {len(d)} 条')"
```

## 相关文件

| 文件 | 作用 |
|------|------|
| `run.py` | 入口脚本（CLI 参数解析 + Cookie 注入 + 爬取编排） |
| `cookie_injector.py` | Cookie 管理（import/export via CDP） |
| `crawler.py` | 核心爬取引擎（增量、滚动、卡片解析） |
| `browser_finder.py` | 浏览器自动检测（macOS/Linux/Windows） |
| `.index_*.json` | 增量索引（自动生成） |
| `requirements.txt` | Python 依赖列表 |
| `venv/` | Python 虚拟环境 |

## 依赖项目

| 项目 | 作用 | 路径 |
|------|------|------|
| agent_edge_launcher | 启动隔离 Edge 实例 | `~/agent_projects/agent_edge_launcher/` |
| Cookie DB (Edge) | 用户登录状态存储 | `~/Library/Application Support/Microsoft Edge Agent Profile/` |

## 注意事项

⚠️ Cookie JSON 文件包含敏感会话信息，**不要上传到公共仓库**
⚠️ 每次爬取前必须启动 Edge Agent Profile
⚠️ Edge 默认在后台运行，不要手动关闭
⚠️ 如果爬取失败，检查：1) Edge 是否运行 2) Cookie 是否过期 3) 网络连接
