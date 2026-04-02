# 飞书论文助手

基于飞书的学术论文管理工具，集论文筛选推送、收藏管理、开源检测于一体。

## ✨ 功能特性

### 📚 论文筛选推送（Kimi）
- 🔍 从 ArXiv RSS 自动获取最新论文
- 🤖 使用 Kimi LLM 智能筛选和评分
- 👤 支持作者追踪（Semantic Scholar ID）
- 📱 自动推送到飞书群聊

### 📥 论文收藏管理
- 📨 自动检测群聊中被回复的论文消息
- 📊 自动写入飞书多维表格
- 🔄 支持去重，避免重复收藏
- 🧠 DeepSeek AI 一句话摘要

### 🔗 开源检测
- 🔍 自动检测论文是否有 GitHub 开源仓库
- 📝 自动更新多维表格开源状态

## 🚀 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写必要配置
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置筛选规则（Kimi 功能）

```bash
# 配置关注的论文主题
cp configs/paper_topics.template.txt configs/paper_topics.md

# 配置追踪的作者
cp configs/authors.template.txt configs/authors.md
```

### 4. 运行

```bash
# 论文筛选推送
python run_kimi.py

# 论文收藏
python collect_papers.py

# 开源检测
python check_opensource.py
```

## ⚙️ 环境变量

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `KIMI_KEY` | 筛选功能 | Kimi (Moonshot) API 密钥 |
| `DEEPSEEK_API_KEY` | 可选 | DeepSeek API 密钥（用于翻译和摘要） |
| `S2_KEY` | 可选 | Semantic Scholar API 密钥 |
| `FEISHU_APP_ID` | ✅ | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | ✅ | 飞书应用 App Secret |
| `FEISHU_CHAT_ID` | ✅ | 飞书群聊 Chat ID |
| `FEISHU_BITABLE_APP_TOKEN` | 收藏功能 | 多维表格 App Token |
| `FEISHU_COLLECT_TABLE_ID` | 收藏功能 | 收藏表 Table ID |

## 📁 项目结构

```
feishu_paper_assistant/
├── .github/workflows/        # GitHub Actions 工作流
│   ├── kimi_daily.yaml       # 每日论文筛选（北京时间 9:30）
│   ├── collect_papers.yaml   # 每日论文收藏（北京时间 23:30）
│   └── check_opensource.yaml # 每周开源检测（周日 23:30）
├── src/
│   ├── kimi/                 # Kimi 论文筛选模块
│   │   ├── main.py
│   │   ├── arxiv_scraper.py
│   │   ├── filter_papers.py
│   │   └── push_to_feishu.py
│   ├── config.py             # 配置模块
│   ├── feishu_api.py         # 飞书 API
│   ├── bitable_client.py     # 多维表格
│   ├── paper_parser.py       # 论文解析
│   ├── deepseek_client.py    # DeepSeek AI
│   └── pwc_client.py         # 开源检测
├── configs/                  # 配置文件
│   ├── config.ini            # 主配置
│   ├── paper_topics.md       # 筛选标准
│   ├── authors.md            # 追踪作者
│   └── translate.md          # 翻译提示词
├── run_kimi.py               # Kimi 筛选入口
├── collect_papers.py         # 收藏脚本
├── check_opensource.py       # 开源检测脚本
├── requirements.txt
└── .env.example
```

## 🔄 GitHub Actions

| 工作流 | 执行时间 | 功能 |
|--------|----------|------|
| `kimi_daily.yaml` | 每天 9:30（北京时间） | ArXiv 论文筛选推送 |
| `collect_papers.yaml` | 每天 23:30（北京时间） | 收藏回复的论文 |
| `check_opensource.yaml` | 每周日 23:30（北京时间） | 检测开源状态 |

### 部署步骤

1. Fork 本仓库
2. 在 **Settings → Secrets** 中添加环境变量
3. 启用 Actions
4. 编辑 `configs/` 下的配置文件

## 📋 飞书应用权限

需要在飞书开放平台开通：
- `im:message` - 读取/发送消息
- `im:chat:readonly` - 读取群聊信息
- `bitable:app` - 多维表格读写

## 📄 License

Apache 2.0
