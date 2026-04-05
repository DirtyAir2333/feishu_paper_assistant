"""
飞书论文收藏机器人 - 飞书API封装
"""

import time
import requests
from typing import List, Dict, Optional

from .config import Config


class FeishuClient:
    """飞书 API 客户端"""
    
    def __init__(self):
        self.base_url = Config.BASE_URL
        self.token = None
        self.headers = {}
        self._init_token()
    
    def _init_token(self):
        """初始化 tenant_access_token"""
        self.token = self._get_tenant_token()
        if self.token:
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
    
    def _get_tenant_token(self) -> Optional[str]:
        """获取 tenant_access_token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        
        try:
            resp = requests.post(url, json={
                "app_id": Config.APP_ID,
                "app_secret": Config.APP_SECRET
            }, timeout=10)
            
            data = resp.json()
            if data.get("code") == 0:
                return data.get("tenant_access_token")
            else:
                print(f"❌ 获取token失败: {data.get('msg')}")
                return None
        except Exception as e:
            print(f"❌ 请求token异常: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.token is not None
    
    def get_chat_messages(self, start_time: int, end_time: int) -> List[Dict]:
        """
        获取群聊消息列表
        
        Args:
            start_time: 起始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
            
        Returns:
            消息列表
        """
        url = f"{self.base_url}/im/v1/messages"
        params = {
            "container_id_type": "chat",
            "container_id": Config.CHAT_ID,
            "page_size": 50,
            "sort_type": "ByCreateTimeDesc"  # 按时间倒序，最新消息在前
        }
        
        all_messages = []
        page_token = None
        
        while True:
            if page_token:
                params["page_token"] = page_token
            
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=10)
                data = resp.json()
                
                if data.get("code") != 0:
                    print(f"❌ 获取消息失败: {data.get('msg')}")
                    break
                
                items = data.get("data", {}).get("items", [])
                all_messages.extend(items)
                
                page_token = data.get("data", {}).get("page_token")
                has_more = data.get("data", {}).get("has_more", False)
                
                if not page_token or not has_more:
                    break
                
                time.sleep(0.1)  # 避免频率限制
                
            except Exception as e:
                print(f"❌ 请求消息异常: {e}")
                break
        
        return all_messages
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """
        获取单条消息详情
        
        Args:
            message_id: 消息ID
            
        Returns:
            消息详情字典
        """
        url = f"{self.base_url}/im/v1/messages/{message_id}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            data = resp.json()
            
            if data.get("code") == 0:
                items = data.get("data", {}).get("items", [])
                return items[0] if items else None
            else:
                print(f"❌ 获取消息详情失败: {data.get('msg')}")
                return None
        except Exception as e:
            print(f"❌ 请求消息详情异常: {e}")
            return None
    
    def get_reply_messages(self, start_time: int, end_time: int) -> List[Dict]:
        """
        获取指定时间范围内的回复消息
        
        Args:
            start_time: 起始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
            
        Returns:
            回复消息列表
        """
        all_messages = self.get_chat_messages(start_time, end_time)
        
        # 筛选出有 parent_id 或 root_id 的消息（即回复消息），并在时间范围内
        reply_messages = []
        for msg in all_messages:
            create_time = int(msg.get("create_time", 0))
            has_parent = msg.get("parent_id") or msg.get("root_id")
            
            # 时间范围过滤 + 是否为回复消息
            if has_parent and start_time <= create_time <= end_time:
                reply_messages.append(msg)
        
        return reply_messages
    
    def send_reply_message(self, parent_message_id: str, content: str) -> Optional[str]:
        """
        回复指定消息（在 thread 中回复）
        
        Args:
            parent_message_id: 被回复的消息ID
            content: 回复的文本内容
            
        Returns:
            发送成功返回消息ID，失败返回None
        """
        url = f"{self.base_url}/im/v1/messages/{parent_message_id}/reply"
        
        payload = {
            "content": f'{{"text": "{content}"}}',
            "msg_type": "text"
        }
        
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            data = resp.json()
            
            if data.get("code") == 0:
                return data.get("data", {}).get("message_id")
            else:
                print(f"❌ 发送回复消息失败: {data.get('msg')}")
                return None
        except Exception as e:
            print(f"❌ 发送回复消息异常: {e}")
            return None
