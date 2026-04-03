#!/usr/bin/env python3
"""
ArXiv 每日论文筛选与推送脚本

功能：
1. 从 ArXiv RSS 获取最新论文
2. 使用 DeepSeek LLM 进行智能筛选和评分
3. 推送筛选结果到飞书群聊

使用方法：
    python run_assistant.py

环境变量要求：
    - DEEPSEEK_API_KEY: DeepSeek API Key（必需）
    - S2_KEY: Semantic Scholar API Key（可选，加速作者查询）
    - FEISHU_APP_ID: 飞书应用 ID（可选，用于推送）
    - FEISHU_APP_SECRET: 飞书应用 Secret（可选，用于推送）
    - FEISHU_CHAT_ID: 飞书群聊 ID（可选，用于推送）
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 运行论文筛选主模块
if __name__ == "__main__":
    import runpy
    runpy.run_module("src.kimi.main", run_name="__main__")
