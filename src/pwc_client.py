"""
飞书论文收藏机器人 - Papers With Code / Hugging Face API 客户端
检索论文是否有开源代码仓库
"""

import re
import requests
from typing import Optional, Dict, Any


class PWCClient:
    """Papers With Code / Hugging Face Papers API 客户端"""
    
    def __init__(self, timeout: int = 10):
        """
        初始化客户端
        
        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.hf_api_base = "https://huggingface.co/api/papers"
        self.arxiv_api_base = "http://export.arxiv.org/api/query"
    
    @staticmethod
    def extract_arxiv_id(arxiv_url: str) -> Optional[str]:
        """
        从 ArXiv URL 中提取论文 ID
        
        Args:
            arxiv_url: ArXiv 论文链接
            
        Returns:
            论文 ID 或 None
        """
        if not arxiv_url:
            return None
        match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', arxiv_url)
        if match:
            return match.group(1)
        return None
    
    def check_opensource(self, arxiv_url: str) -> Dict[str, Any]:
        """
        检查论文是否有开源代码
        
        Args:
            arxiv_url: ArXiv 论文链接
            
        Returns:
            包含开源信息的字典:
            {
                "is_opensource": bool,
                "github_repo": Optional[str],
                "title": Optional[str],
                "upvotes": int
            }
        """
        result = {
            "is_opensource": False,
            "github_repo": None,
            "title": None,
            "upvotes": 0
        }
        
        arxiv_id = self.extract_arxiv_id(arxiv_url)
        if not arxiv_id:
            return result
        
        try:
            # 查询 Hugging Face Papers API
            api_url = f"{self.hf_api_base}/{arxiv_id}"
            response = requests.get(api_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                result["title"] = data.get("title")
                result["upvotes"] = data.get("upvotes", 0)
                
                github_repo = data.get("githubRepo")
                if github_repo:
                    result["is_opensource"] = True
                    result["github_repo"] = github_repo
        except requests.RequestException:
            pass
        
        return result
    
    def search_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        通过论文标题搜索（使用 arXiv API）
        
        Args:
            title: 论文标题
            
        Returns:
            论文信息或 None
        """
        try:
            import urllib.parse
            # 使用标题搜索 arXiv
            query = urllib.parse.quote(f'ti:"{title}"')
            url = f"{self.arxiv_api_base}?search_query={query}&max_results=1"
            
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                # 提取 arxiv ID
                arxiv_ids = re.findall(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', response.text)
                if arxiv_ids:
                    arxiv_url = f"https://arxiv.org/abs/{arxiv_ids[0]}"
                    return self.check_opensource(arxiv_url)
        except requests.RequestException:
            pass
        
        return None
