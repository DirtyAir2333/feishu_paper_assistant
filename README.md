<div align="center">

# 📚 Feishu Paper Assistant

**基于飞书的智能学术论文管理工具**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek-green.svg)](https://deepseek.com)

[English](#english) | [简体中文](#简体中文)

</div>

---

## 简体中文

### 📖 简介

Feishu Paper Assistant 是一个基于飞书（Lark）的学术论文管理工具，集成了 **论文智能筛选推送**、**群聊收藏管理** 和 **GitHub 开源检测** 三大核心功能。通过 DeepSeek LLM 实现智能论文评分，帮助研究人员高效追踪最新学术动态。

### ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🔍 **论文筛选推送** | 从 ArXiv RSS 自动获取最新论文，使用 DeepSeek-Reasoner 智能评分筛选 |
| 👤 **作者追踪** | 基于 Semantic Scholar ID 自动追踪关注作者的新论文 |
| 📥 **群聊收藏** | 自动检测飞书群聊中被回复的论文，写入多维表格 |
| 🧠 **AI 摘要** | DeepSeek 一句话总结论文核心贡献 |
| 🔗 **开源检测** | 通过 Papers With Code API 检测论文 GitHub 开源仓库 |
| ⏰ **自动化** | GitHub Actions 定时执行，无需人工干预 |

### 🚀 快速开始

#### 1. 克隆仓库

```bash
git clone https://github.com/DirtyAir2333/feishu_paper_assistant.git
cd feishu_paper_assistant
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写你的 API 密钥
```

#### 4. 配置筛选规则

```bash
# 配置关注的论文主题（用于 LLM 评分）
cp configs/paper_topics.template.txt configs/paper_topics.md

# 配置追踪的作者（Semantic Scholar ID）
cp configs/authors.template.txt configs/authors.md
```

#### 5. 运行

```bash
# 论文筛选推送
python run_assistant.py

# 论文收藏（群聊回复的论文）
python collect_papers.py

# 开源检测
python check_opensource.py
```

### ⚙️ 环境变量

| 变量名 | 必需 | 说明 |
|--------|:----:|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API 密钥（筛选/翻译/摘要） |
| `FEISHU_APP_ID` | ✅ | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | ✅ | 飞书应用 App Secret |
| `FEISHU_CHAT_ID` | ✅ | 飞书群聊 Chat ID |
| `FEISHU_BITABLE_APP_TOKEN` | 收藏功能 | 多维表格 App Token |
| `FEISHU_COLLECT_TABLE_ID` | 收藏功能 | 收藏表 Table ID |
| `S2_KEY` | 可选 | Semantic Scholar API（加速作者查询） |

### 📁 项目结构

```
feishu_paper_assistant/
├── .github/workflows/          # GitHub Actions 工作流
│   ├── kimi_daily.yaml         # 每日论文筛选（北京时间 9:30）
│   ├── collect_papers.yaml     # 每日论文收藏（北京时间 23:30）
│   └── check_opensource.yaml   # 每周开源检测（周日 23:30）
├── src/
│   ├── kimi/                   # 论文筛选模块
│   │   ├── main.py             # 主逻辑
│   │   ├── arxiv_scraper.py    # ArXiv 抓取
│   │   ├── filter_papers.py    # LLM 筛选评分
│   │   └── push_to_feishu.py   # 推送到飞书
│   ├── feishu_api.py           # 飞书 API 封装
│   ├── bitable_client.py       # 多维表格操作
│   ├── paper_parser.py         # 论文解析
│   ├── deepseek_client.py      # DeepSeek AI 客户端
│   └── pwc_client.py           # Papers With Code 开源检测
├── configs/                    # 配置文件
│   ├── config.ini              # 主配置（ArXiv 分类、评分阈值等）
│   ├── paper_topics.md         # 论文筛选标准
│   ├── authors.md              # 追踪作者列表
│   └── translate.md            # 翻译提示词
├── run_assistant.py            # 筛选推送入口
├── collect_papers.py           # 收藏脚本
├── check_opensource.py         # 开源检测脚本
├── requirements.txt
└── .env.example
```

### 🔄 GitHub Actions

| 工作流 | 执行时间（北京时间） | 功能 |
|--------|:--------------------:|------|
| `kimi_daily.yaml` | 每天 09:30 | ArXiv 论文筛选推送 |
| `collect_papers.yaml` | 每天 23:30 | 收藏群聊回复的论文 |
| `check_opensource.yaml` | 每周日 23:30 | 批量检测开源状态 |

**部署步骤：**

1. Fork 本仓库
2. 在 **Settings → Secrets and variables → Actions** 中添加环境变量
3. 启用 GitHub Actions
4. 自定义 `configs/` 下的配置文件

### 📋 飞书应用权限

在 [飞书开放平台](https://open.feishu.cn/) 创建应用后，需开通以下权限：

- `im:message` - 读取和发送消息
- `im:message.group_at_msg:readonly` - 读取群聊消息
- `im:message:send_as_bot` - 以机器人身份发送消息
- `im:chat:readonly` - 读取群聊信息
- `bitable:app` - 多维表格读写

### 🤖 DeepSeek 模型选择

本项目使用 DeepSeek-V3.2 (128K 上下文)：

| 场景 | 模型 | 说明 |
|------|------|------|
| 论文筛选评分 | `deepseek-reasoner` | 思考模式，推理质量更高 |
| 论文翻译 | `deepseek-chat` | 非思考模式，响应速度更快 |
| 摘要总结 | `deepseek-chat` | 非思考模式，响应速度更快 |

---

## 🙏 致谢

本项目的开发参考并借鉴了以下优秀的开源项目：

- **[gpt_paper_assistant](https://github.com/tatsu-lab/gpt_paper_assistant)** - 论文筛选评分的核心思路、ArXiv 抓取逻辑、作者匹配机制
- **[feishu_paper](https://github.com/caozx1110/feishu_paper)** - 飞书消息推送、多维表格操作的实现参考

感谢这些项目的作者们的开源贡献！

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

---

<div align="center">

**如果这个项目对你有帮助，欢迎 ⭐ Star！**

</div>
