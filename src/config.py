"""
飞书论文收藏机器人 - 配置模块
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """配置类"""
    
    # 飞书应用配置
    APP_ID = os.getenv('FEISHU_APP_ID')
    APP_SECRET = os.getenv('FEISHU_APP_SECRET')
    
    # 群聊配置
    CHAT_ID = os.getenv('FEISHU_CHAT_ID')
    
    # 多维表格配置
    BITABLE_APP_TOKEN = os.getenv('FEISHU_BITABLE_APP_TOKEN')
    COLLECT_TABLE_ID = os.getenv('FEISHU_COLLECT_TABLE_ID')
    
    # API 基础URL
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    # 日志级别
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> bool:
        """验证必填配置"""
        required = [
            ('FEISHU_APP_ID', cls.APP_ID),
            ('FEISHU_APP_SECRET', cls.APP_SECRET),
            ('FEISHU_CHAT_ID', cls.CHAT_ID),
            ('FEISHU_BITABLE_APP_TOKEN', cls.BITABLE_APP_TOKEN),
            ('FEISHU_COLLECT_TABLE_ID', cls.COLLECT_TABLE_ID),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            print(f"❌ 缺少必填配置: {', '.join(missing)}")
            return False
        
        return True
