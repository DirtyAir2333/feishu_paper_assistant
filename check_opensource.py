#!/usr/bin/env python3
"""
飞书论文收藏机器人 - 开源状态检测脚本
每周检测多维表格中未开源的论文是否已有开源仓库
"""

import time
import requests
from typing import List, Dict, Any

from src.config import Config
from src.feishu_api import FeishuClient
from src.pwc_client import PWCClient


def check_opensource_status():
    """检测并更新论文开源状态"""
    print("🔍 开源状态检测启动...")
    print("=" * 50)
    
    # 验证配置
    if not Config.validate():
        print("❌ 配置验证失败，请检查 .env 文件")
        return
    
    # 初始化飞书客户端
    print("📡 正在连接飞书...")
    feishu = FeishuClient()
    
    if not feishu.is_authenticated():
        print("❌ 飞书认证失败")
        return
    
    print("✅ 飞书连接成功")
    
    # 初始化 PWC 客户端
    pwc = PWCClient()
    
    # 获取所有未开源的论文记录
    print("📋 正在获取未开源论文列表...")
    records = get_not_opensource_records(feishu.token)
    
    if not records:
        print("📭 没有需要检测的论文")
        return
    
    print(f"📄 找到 {len(records)} 篇未开源论文，开始检测...")
    
    # 检测每篇论文
    updated = 0
    checked = 0
    
    for record in records:
        record_id = record.get("record_id")
        fields = record.get("fields", {})
        
        # 获取论文链接
        link_field = fields.get("论文链接", {})
        arxiv_url = link_field.get("link", "") if isinstance(link_field, dict) else ""
        
        if not arxiv_url:
            continue
        
        title_field = fields.get("论文题目", "未知")
        # 处理富文本格式的标题
        if isinstance(title_field, list) and title_field:
            title = title_field[0].get("text", "未知")[:40]
        else:
            title = str(title_field)[:40]
        checked += 1
        
        print(f"  🔍 检测: {title}...")
        
        # 检测开源状态
        result = pwc.check_opensource(arxiv_url)
        
        if result.get("is_opensource") and result.get("github_repo"):
            github_repo = result["github_repo"]
            print(f"  🎉 发现开源: {github_repo}")
            
            # 更新记录
            if update_record_opensource(feishu.token, record_id, github_repo):
                print(f"  ✅ 已更新记录")
                updated += 1
            else:
                print(f"  ❌ 更新失败")
        else:
            print(f"  ⚪ 暂无开源")
        
        time.sleep(0.5)  # 避免频率限制
    
    # 输出统计
    print("=" * 50)
    print(f"📊 完成！检测 {checked} 篇，更新 {updated} 篇为已开源")


def get_not_opensource_records(token: str) -> List[Dict[str, Any]]:
    """
    获取所有未开源的论文记录
    
    Args:
        token: 飞书访问令牌
        
    Returns:
        记录列表
    """
    url = f"{Config.BASE_URL}/bitable/v1/apps/{Config.BITABLE_APP_TOKEN}/tables/{Config.COLLECT_TABLE_ID}/records/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 筛选未开源的记录
    payload = {
        "filter": {
            "conjunction": "and",
            "conditions": [{
                "field_name": "是否开源",
                "operator": "is",
                "value": ["未开源"]
            }]
        },
        "page_size": 500
    }
    
    all_records = []
    page_token = None
    
    while True:
        if page_token:
            payload["page_token"] = page_token
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            data = resp.json()
            
            if data.get("code") != 0:
                print(f"  ⚠️ API错误: {data.get('msg')}")
                break
            
            items = data.get("data", {}).get("items", [])
            all_records.extend(items)
            
            # 检查是否有更多页
            page_token = data.get("data", {}).get("page_token")
            if not page_token:
                break
                
        except requests.RequestException as e:
            print(f"  ❌ 请求失败: {e}")
            break
    
    return all_records


def update_record_opensource(token: str, record_id: str, github_repo: str) -> bool:
    """
    更新记录的开源状态
    
    Args:
        token: 飞书访问令牌
        record_id: 记录ID
        github_repo: GitHub仓库链接
        
    Returns:
        是否更新成功
    """
    url = f"{Config.BASE_URL}/bitable/v1/apps/{Config.BITABLE_APP_TOKEN}/tables/{Config.COLLECT_TABLE_ID}/records/{record_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "fields": {
            "是否开源": "已开源",
            "仓库链接": {
                "link": github_repo,
                "text": github_repo
            }
        }
    }
    
    try:
        resp = requests.put(url, headers=headers, json=payload, timeout=10)
        data = resp.json()
        return data.get("code") == 0
    except requests.RequestException:
        return False


def main():
    """入口函数"""
    try:
        check_opensource_status()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"❌ 运行异常: {e}")
        raise


if __name__ == "__main__":
    main()
