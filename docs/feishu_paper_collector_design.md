# 飞书论文收藏机器人 - 实现方案

## 📋 需求概述

### 场景描述
1. 现有机器人每天推送论文消息卡片到飞书群
2. 用户在感兴趣的论文消息下**回复**（如"收藏"、"mark"等）
3. **每天晚上 11 点**，自动检测当天被回复的论文，统一写入多维表格

### 目标
- 实现"一键收藏"论文的功能
- 无需手动复制粘贴，自动提取论文信息
- 数据结构化存储，便于后续检索和管理
- **无需部署服务器/云函数，GitHub Actions 定时任务即可**

---

## 🏗️ 技术架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   飞书群聊       │     │  GitHub Actions  │     │  飞书多维表格    │
│  (用户回复消息)   │     │  (定时任务 cron) │     │  (数据存储)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        ▲
        │                       ▼                        │
        │               ┌──────────────────┐             │
        └──────────────▶│   飞书消息 API    │─────────────┘
                        │  (拉取群聊消息)   │
                        └──────────────────┘
```

### 工作流程

```
每天 23:00 (北京时间)
    │
    ▼
┌─────────────────────────────────┐
│ 1. 获取群聊今日消息列表          │
│    GET /im/v1/messages          │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ 2. 筛选出"回复类型"的消息        │
│    (有 parent_id 的消息)        │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ 3. 获取被回复的原消息（论文卡片） │
│    GET /im/v1/messages/{id}     │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ 4. 解析论文信息                  │
│    (ArXiv ID, 标题, 评分等)     │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ 5. 去重 + 写入多维表格           │
│    POST /bitable/v1/.../records │
└─────────────────────────────────┘
```

### 核心优势

| 对比项 | Webhook 实时方案 | ✅ 定时拉取方案 |
|-------|-----------------|----------------|
| 部署复杂度 | 需要云函数/VPS | GitHub Actions 即可 |
| 成本 | 可能收费 | 免费 |
| 维护 | 需要监控服务可用性 | 无需维护 |
| 延迟 | 实时 | 最多延迟一天 |

---

## 🔄 数据流详解

### Step 1: 获取群聊消息列表

API: `GET /open-apis/im/v1/messages`

```python
# 获取今天的消息
params = {
    "container_id_type": "chat",
    "container_id": CHAT_ID,
    "start_time": today_start_timestamp,  # 今天 00:00
    "end_time": now_timestamp,             # 当前时间
    "page_size": 50
}
```

### Step 2: 筛选回复消息

```python
# 找出有 parent_id 的消息（即回复消息）
reply_messages = [
    msg for msg in messages 
    if msg.get('parent_id') or msg.get('root_id')
]
```

### Step 3: 获取原消息并解析

对每个回复消息，获取其 `parent_id` 对应的原消息（论文卡片），提取：
```json
{
  "arxiv_id": "2603.12345",
  "title": "论文标题",
  "title_zh": "中文标题",
  "arxiv_url": "https://arxiv.org/abs/2603.12345",
  "relevance": 8,
  "novelty": 7
}
```

### Step 4: 写入多维表格

复用 `feishu_bitable_connector.py` 的逻辑，批量写入。

---

## 📁 项目结构设计

```
kimi_paper_assistant/
├── .github/
│   └── workflows/
│       ├── cron_runs.yaml           # 每天推送论文（已有）
│       └── collect_papers.yaml      # 每天收藏论文（新增）
├── collect_papers.py                # 收藏论文主脚本（新增）
├── feishu_api.py                    # 飞书 API 封装（新增）
├── push_to_feishu.py                # 推送论文（已有）
└── ...
```

---

## 🔑 环境变量

```bash
# 飞书应用配置（已有）
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_CHAT_ID=oc_xxx              # 群聊 ID

# 多维表格配置（新增）
FEISHU_BITABLE_APP_TOKEN=xxx       # 多维表格的 app_token
FEISHU_COLLECT_TABLE_ID=tblxxx     # 收藏表的 table_id
```

---

## 📝 核心代码设计

### 1. GitHub Actions 工作流 (`.github/workflows/collect_papers.yaml`)

```yaml
name: Collect replied papers

on:
  schedule:
    # 每天北京时间 23:00 (UTC 15:00) 执行
    - cron: '0 15 * * *'
  workflow_dispatch:  # 允许手动触发

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Collect papers
      env:
        FEISHU_APP_ID: ${{ secrets.FEISHU_APP_ID }}
        FEISHU_APP_SECRET: ${{ secrets.FEISHU_APP_SECRET }}
        FEISHU_CHAT_ID: ${{ secrets.FEISHU_CHAT_ID }}
        FEISHU_BITABLE_APP_TOKEN: ${{ secrets.FEISHU_BITABLE_APP_TOKEN }}
        FEISHU_COLLECT_TABLE_ID: ${{ secrets.FEISHU_COLLECT_TABLE_ID }}
      run: python collect_papers.py
```

### 2. 主脚本 (`collect_papers.py`)

```python
#!/usr/bin/env python3
"""
定时收藏论文脚本
每天检测群聊中被回复的论文消息，写入多维表格
"""

import os
import re
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

# 配置
APP_ID = os.getenv('FEISHU_APP_ID')
APP_SECRET = os.getenv('FEISHU_APP_SECRET')
CHAT_ID = os.getenv('FEISHU_CHAT_ID')
BITABLE_APP_TOKEN = os.getenv('FEISHU_BITABLE_APP_TOKEN')
TABLE_ID = os.getenv('FEISHU_COLLECT_TABLE_ID')

BASE_URL = "https://open.feishu.cn/open-apis"


class FeishuClient:
    """飞书 API 客户端"""
    
    def __init__(self):
        self.token = self._get_tenant_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _get_tenant_token(self) -> str:
        """获取 tenant_access_token"""
        url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        })
        return resp.json().get("tenant_access_token")
    
    def get_chat_messages(self, start_time: int, end_time: int) -> List[Dict]:
        """获取群聊消息列表"""
        url = f"{BASE_URL}/im/v1/messages"
        params = {
            "container_id_type": "chat",
            "container_id": CHAT_ID,
            "start_time": str(start_time),
            "end_time": str(end_time),
            "page_size": 50
        }
        
        all_messages = []
        page_token = None
        
        while True:
            if page_token:
                params["page_token"] = page_token
            
            resp = requests.get(url, headers=self.headers, params=params)
            data = resp.json().get("data", {})
            
            items = data.get("items", [])
            all_messages.extend(items)
            
            page_token = data.get("page_token")
            if not page_token or not data.get("has_more"):
                break
            
            time.sleep(0.1)  # 避免频率限制
        
        return all_messages
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """获取单条消息详情"""
        url = f"{BASE_URL}/im/v1/messages/{message_id}"
        resp = requests.get(url, headers=self.headers)
        data = resp.json()
        
        if data.get("code") == 0:
            return data.get("data", {}).get("items", [{}])[0]
        return None


class BitableClient:
    """飞书多维表格客户端"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def check_exists(self, arxiv_id: str) -> bool:
        """检查论文是否已存在"""
        url = f"{BASE_URL}/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{TABLE_ID}/records/search"
        payload = {
            "filter": {
                "conjunction": "and",
                "conditions": [{
                    "field_name": "ArXiv ID",
                    "operator": "contains",
                    "value": [arxiv_id]
                }]
            }
        }
        
        try:
            resp = requests.post(url, headers=self.headers, json=payload)
            data = resp.json()
            return len(data.get("data", {}).get("items", [])) > 0
        except:
            return False
    
    def insert_record(self, fields: Dict) -> bool:
        """插入一条记录"""
        url = f"{BASE_URL}/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{TABLE_ID}/records"
        payload = {"fields": fields}
        
        resp = requests.post(url, headers=self.headers, json=payload)
        return resp.json().get("code") == 0


def parse_paper_from_message(message: Dict) -> Optional[Dict]:
    """从论文消息中解析信息"""
    content_str = message.get("body", {}).get("content", "")
    if not content_str:
        return None
    
    try:
        content = json.loads(content_str)
    except json.JSONDecodeError:
        return None
    
    paper_info = {}
    zh_content = content.get("zh_cn", {})
    
    # 遍历消息内容提取信息
    for line in zh_content.get("content", []):
        for item in line:
            tag = item.get("tag", "")
            text = item.get("text", "")
            href = item.get("href", "")
            
            # 提取 ArXiv 链接
            if tag == "a" and "arxiv.org" in href:
                paper_info["arxiv_url"] = href
                match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d+\.\d+)", href)
                if match:
                    paper_info["arxiv_id"] = match.group(1)
            
            # 提取标题
            if text.startswith("论文题目:"):
                paper_info["title"] = text.replace("论文题目:", "").strip()
            
            if text.startswith("中文翻译:"):
                paper_info["title_zh"] = text.replace("中文翻译:", "").strip()
            
            # 提取评分
            if "相关度:" in text:
                match = re.search(r"\((\d+)/10\)", text)
                if match:
                    paper_info["relevance"] = int(match.group(1))
            
            if "新颖度:" in text:
                match = re.search(r"\((\d+)/10\)", text)
                if match:
                    paper_info["novelty"] = int(match.group(1))
    
    return paper_info if paper_info.get("arxiv_id") else None


def main():
    print("🚀 开始收藏论文...")
    
    # 初始化客户端
    feishu = FeishuClient()
    bitable = BitableClient(feishu.token)
    
    # 计算今天的时间范围（北京时间）
    now = datetime.utcnow() + timedelta(hours=8)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_ts = int((today_start - timedelta(hours=8)).timestamp() * 1000)  # 转回 UTC
    end_ts = int((now - timedelta(hours=8)).timestamp() * 1000)
    
    print(f"📅 检查时间范围: {today_start.strftime('%Y-%m-%d')} 00:00 - {now.strftime('%H:%M')}")
    
    # 获取今日消息
    messages = feishu.get_chat_messages(start_ts, end_ts)
    print(f"📨 获取到 {len(messages)} 条消息")
    
    # 筛选回复消息
    reply_messages = [
        msg for msg in messages
        if msg.get("parent_id") or msg.get("root_id")
    ]
    print(f"💬 其中 {len(reply_messages)} 条是回复消息")
    
    # 去重：收集被回复的论文消息 ID
    paper_message_ids = set()
    for msg in reply_messages:
        parent_id = msg.get("parent_id") or msg.get("root_id")
        if parent_id:
            paper_message_ids.add(parent_id)
    
    print(f"📄 涉及 {len(paper_message_ids)} 篇论文")
    
    # 处理每篇论文
    collected = 0
    skipped = 0
    
    for msg_id in paper_message_ids:
        # 获取原消息（论文卡片）
        original_msg = feishu.get_message(msg_id)
        if not original_msg:
            print(f"  ⚠️ 无法获取消息 {msg_id}")
            continue
        
        # 解析论文信息
        paper_info = parse_paper_from_message(original_msg)
        if not paper_info:
            print(f"  ⚠️ 无法解析论文信息 {msg_id}")
            continue
        
        arxiv_id = paper_info["arxiv_id"]
        
        # 检查是否已存在
        if bitable.check_exists(arxiv_id):
            print(f"  ⏭️ 已存在: {arxiv_id}")
            skipped += 1
            continue
        
        # 写入多维表格
        fields = {
            "ArXiv ID": {
                "link": paper_info.get("arxiv_url", ""),
                "text": arxiv_id
            },
            "标题": paper_info.get("title", ""),
            "中文标题": paper_info.get("title_zh", ""),
            "相关度": paper_info.get("relevance", 0),
            "新颖度": paper_info.get("novelty", 0),
            "收藏时间": int(datetime.now().timestamp() * 1000)
        }
        
        if bitable.insert_record(fields):
            print(f"  ✅ 已收藏: {arxiv_id}")
            collected += 1
        else:
            print(f"  ❌ 收藏失败: {arxiv_id}")
        
        time.sleep(0.2)  # 避免频率限制
    
    print(f"\n📊 完成！收藏 {collected} 篇，跳过 {skipped} 篇")


if __name__ == "__main__":
    main()
```

---

## 📊 多维表格字段设计

| 字段名 | 类型 | 说明 |
|-------|------|------|
| ArXiv ID | 超链接 (15) | 链接到原文 |
| 标题 | 文本 (1) | 英文标题 |
| 中文标题 | 文本 (1) | 翻译后的标题 |
| 相关度 | 数字 (2) | 1-10 评分 |
| 新颖度 | 数字 (2) | 1-10 评分 |
| 收藏时间 | 日期 (5) | 自动记录 |
| 阅读状态 | 单选 (3) | 未读/已读/精读 |
| 备注 | 文本 (1) | 手动添加备注 |

---

## ⚠️ 注意事项

1. **飞书应用权限**：需要开通以下权限
   - `im:message:readonly` - 读取群聊消息
   - `im:message` - 获取消息详情
   - `bitable:app` - 多维表格读写

2. **GitHub Actions Secrets**：需要添加以下密钥
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
   - `FEISHU_CHAT_ID`
   - `FEISHU_BITABLE_APP_TOKEN`
   - `FEISHU_COLLECT_TABLE_ID`

3. **消息解析**：
   - 依赖 ArXiv 链接提取 `arxiv_id`（最可靠）
   - 建议推送消息格式保持稳定

4. **去重机制**：
   - 基于 ArXiv ID 去重
   - 同一篇论文只收藏一次

---

## 📅 开发计划

| 阶段 | 任务 | 预估 |
|-----|------|-----|
| P0 | 编写 `collect_papers.py` 脚本 | 0.5天 |
| P0 | 配置 GitHub Actions workflow | 0.5天 |
| P1 | 本地测试 + 调试消息解析 | 0.5天 |
| P2 | 配置 Secrets + 上线测试 | 0.5天 |

---

## 🔗 参考资料

- [飞书获取群聊消息列表](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/list)
- [飞书获取消息详情](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/get)
- [飞书多维表格 API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/create)
- feishu_paper 项目（本地参考，多维表格写入逻辑）
