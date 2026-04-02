#!/usr/bin/env python3
"""
飞书论文收藏机器人 - 主脚本
定时检测群聊中被回复的论文消息，写入多维表格
"""

import time
from datetime import datetime, timedelta
from typing import Set

from src.config import Config
from src.feishu_api import FeishuClient
from src.bitable_client import BitableClient
from src.paper_parser import parse_paper_from_message, build_record_fields


def get_today_time_range() -> tuple:
    """
    获取今天的时间范围（北京时间）
    
    Returns:
        (start_timestamp_ms, end_timestamp_ms)
    """
    # 获取当前北京时间
    now = datetime.utcnow() + timedelta(hours=8)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 转回 UTC 时间戳（毫秒）
    start_ts = int((today_start - timedelta(hours=8)).timestamp() * 1000)
    end_ts = int((now - timedelta(hours=8)).timestamp() * 1000)
    
    return start_ts, end_ts


def collect_papers():
    """收藏论文主函数"""
    print("🚀 飞书论文收藏机器人启动...")
    print("=" * 50)
    
    # 验证配置
    if not Config.validate():
        print("❌ 配置验证失败，请检查 .env 文件")
        return
    
    # 初始化飞书客户端
    print("📡 正在连接飞书...")
    feishu = FeishuClient()
    
    if not feishu.is_authenticated():
        print("❌ 飞书认证失败，请检查 APP_ID 和 APP_SECRET")
        return
    
    print("✅ 飞书连接成功")
    
    # 初始化多维表格客户端
    bitable = BitableClient(feishu.token)
    
    # 获取今天的时间范围
    start_ts, end_ts = get_today_time_range()
    
    now = datetime.utcnow() + timedelta(hours=8)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"📅 检查时间范围: {today_start.strftime('%Y-%m-%d')} 00:00 - {now.strftime('%H:%M')}")
    
    # 获取今日回复消息
    print("📨 正在获取群聊消息...")
    reply_messages = feishu.get_reply_messages(start_ts, end_ts)
    print(f"💬 发现 {len(reply_messages)} 条回复消息")
    
    if not reply_messages:
        print("📭 今日暂无回复消息")
        return
    
    # 去重：收集被回复的论文消息 ID
    paper_message_ids: Set[str] = set()
    for msg in reply_messages:
        parent_id = msg.get("parent_id") or msg.get("root_id")
        if parent_id:
            paper_message_ids.add(parent_id)
    
    print(f"📄 涉及 {len(paper_message_ids)} 条被回复的消息")
    
    # 处理每篇论文
    collected = 0
    skipped = 0
    failed = 0
    
    for msg_id in paper_message_ids:
        # 获取原消息（论文卡片）
        original_msg = feishu.get_message(msg_id)
        if not original_msg:
            print(f"  ⚠️ 无法获取消息: {msg_id[:20]}...")
            failed += 1
            continue
        
        # 解析论文信息
        paper_info = parse_paper_from_message(original_msg)
        if not paper_info:
            print(f"  ⚠️ 非论文消息或解析失败: {msg_id[:20]}...")
            continue
        
        arxiv_id = paper_info["arxiv_id"]
        
        # 检查是否已存在
        if bitable.check_exists(arxiv_id):
            print(f"  ⏭️ 已存在: {arxiv_id}")
            skipped += 1
            continue
        
        # 构建字段并写入
        fields = build_record_fields(paper_info)
        
        if bitable.insert_record(fields):
            title = paper_info.get("title_zh") or paper_info.get("title") or arxiv_id
            print(f"  ✅ 已收藏: {arxiv_id} - {title[:30]}...")
            collected += 1
        else:
            print(f"  ❌ 收藏失败: {arxiv_id}")
            failed += 1
        
        time.sleep(0.2)  # 避免频率限制
    
    # 输出统计
    print("=" * 50)
    print(f"📊 完成！收藏 {collected} 篇，跳过 {skipped} 篇，失败 {failed} 篇")


def main():
    """入口函数"""
    try:
        collect_papers()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"❌ 运行异常: {e}")
        raise


if __name__ == "__main__":
    main()
