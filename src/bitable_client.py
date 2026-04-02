"""
飞书论文收藏机器人 - 多维表格操作
"""

import requests
from typing import Dict, Optional

from .config import Config


class BitableClient:
    """飞书多维表格客户端"""
    
    def __init__(self, token: str):
        """
        初始化多维表格客户端
        
        Args:
            token: tenant_access_token
        """
        self.token = token
        self.base_url = Config.BASE_URL
        self.app_token = Config.BITABLE_APP_TOKEN
        self.table_id = Config.COLLECT_TABLE_ID
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def check_exists(self, arxiv_id: str) -> bool:
        """
        检查论文是否已存在
        
        Args:
            arxiv_id: ArXiv论文ID
            
        Returns:
            是否存在
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/search"
        
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
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            data = resp.json()
            
            if data.get("code") == 0:
                items = data.get("data", {}).get("items", [])
                return len(items) > 0
            else:
                print(f"⚠️ 检查存在性失败: {data.get('msg')}")
                return False
        except Exception as e:
            print(f"⚠️ 检查存在性异常: {e}")
            return False
    
    def insert_record(self, fields: Dict) -> bool:
        """
        插入一条记录
        
        Args:
            fields: 字段数据字典
            
        Returns:
            是否成功
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        
        payload = {"fields": fields}
        
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            data = resp.json()
            
            if data.get("code") == 0:
                return True
            else:
                print(f"❌ 插入记录失败: {data.get('msg')}")
                return False
        except Exception as e:
            print(f"❌ 插入记录异常: {e}")
            return False
    
    def batch_insert_records(self, records: list) -> int:
        """
        批量插入记录
        
        Args:
            records: 记录列表，每个元素是 fields 字典
            
        Returns:
            成功插入的数量
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/batch_create"
        
        payload = {
            "records": [{"fields": fields} for fields in records]
        }
        
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
            data = resp.json()
            
            if data.get("code") == 0:
                return len(data.get("data", {}).get("records", []))
            else:
                print(f"❌ 批量插入失败: {data.get('msg')}")
                return 0
        except Exception as e:
            print(f"❌ 批量插入异常: {e}")
            return 0
    
    def get_table_fields(self) -> Optional[list]:
        """
        获取表格字段列表
        
        Returns:
            字段列表
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            data = resp.json()
            
            if data.get("code") == 0:
                return data.get("data", {}).get("items", [])
            else:
                print(f"❌ 获取字段失败: {data.get('msg')}")
                return None
        except Exception as e:
            print(f"❌ 获取字段异常: {e}")
            return None
