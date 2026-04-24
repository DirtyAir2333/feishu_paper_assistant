"""
飞书论文收藏机器人 - DeepSeek API 封装
用于论文摘要的AI总结
"""

import os
import requests
from typing import Optional

from .config import Config

FAST_MODEL = "deepseek-v4-flash"


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.enabled = bool(self.api_key)
    
    def summarize_abstract(self, abstract: str, title: str = "") -> Optional[str]:
        """
        使用DeepSeek对论文摘要进行一句话总结
        
        Args:
            abstract: 论文摘要原文
            title: 论文标题（可选，用于辅助理解）
            
        Returns:
            一句话总结，失败返回None
        """
        if not self.enabled:
            return None
        
        if not abstract or len(abstract.strip()) < 10:
            return None
        
        prompt = self._build_prompt(abstract, title)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": FAST_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个学术论文摘要总结助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3,
                    "thinking": {"type": "disabled"}
                },
                timeout=30
            )
            
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                summary = data["choices"][0]["message"]["content"].strip()
                return summary
            else:
                print(f"⚠️ DeepSeek响应异常: {data}")
                return None
                
        except Exception as e:
            print(f"⚠️ DeepSeek API调用失败: {e}")
            return None
    
    def _build_prompt(self, abstract: str, title: str = "") -> str:
        """构建提示词"""
        # 从配置文件读取提示词，如果没有则使用默认
        prompt_template = Config.DEEPSEEK_PROMPT or self._default_prompt()
        
        return prompt_template.format(
            title=title,
            abstract=abstract
        )
    
    def _default_prompt(self) -> str:
        """默认提示词"""
        return """请用一句简洁的中文总结以下论文摘要的核心贡献和方法：

论文标题：{title}

摘要内容：
{abstract}

要求：
1. 只用一句话（不超过100字）
2. 突出论文的核心创新点或方法
3. 使用学术但易懂的语言
4. 直接给出总结，不要有任何前缀"""
