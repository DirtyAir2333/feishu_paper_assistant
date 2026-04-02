# 飞书论文收藏机器人

自动检测飞书群聊中被回复的论文消息，收藏到多维表格。

## 功能

- 📨 自动获取群聊中的回复消息
- 📄 解析被回复的论文卡片信息
- 📊 自动写入飞书多维表格
- 🔄 自动去重，避免重复收藏
- ⏰ 支持 GitHub Actions 定时执行

## 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```bash
cp .env.example .env
```

需要配置：
- `FEISHU_APP_ID` - 飞书应用ID
- `FEISHU_APP_SECRET` - 飞书应用密钥
- `FEISHU_CHAT_ID` - 群聊ID
- `FEISHU_BITABLE_APP_TOKEN` - 多维表格Token
- `FEISHU_COLLECT_TABLE_ID` - 收藏表ID

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行

```bash
python collect_papers.py
```

## 飞书应用权限

需要在飞书开放平台开通以下权限：

- `im:message` - 读取消息
- `im:chat:readonly` - 读取群聊信息
- `bitable:app` - 多维表格读写

## 多维表格字段

建议创建以下字段：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| ArXiv ID | 超链接 | 论文ID，链接到原文 |
| 标题 | 文本 | 英文标题 |
| 中文标题 | 文本 | 中文翻译 |
| 相关度 | 数字 | 1-10 评分 |
| 新颖度 | 数字 | 1-10 评分 |
| 收藏时间 | 日期 | 自动记录 |
| 链接 | 超链接 | ArXiv链接 |

## 项目结构

```
feishu_paper_assistant/
├── .github/workflows/     # GitHub Actions
├── src/                   # 源代码
│   ├── config.py          # 配置模块
│   ├── feishu_api.py      # 飞书API
│   ├── bitable_client.py  # 多维表格
│   └── paper_parser.py    # 论文解析
├── tests/                 # 测试文件
├── collect_papers.py      # 主脚本
├── requirements.txt       # 依赖
└── .env.example           # 配置示例
```

## License

MIT
