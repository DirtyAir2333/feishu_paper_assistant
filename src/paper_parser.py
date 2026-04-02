"""
飞书论文收藏机器人 - 论文信息解析
"""

import re
import json
from typing import Dict, Optional
from datetime import datetime


def parse_paper_from_message(message: Dict) -> Optional[Dict]:
    """
    从论文消息中解析论文信息
    
    Args:
        message: 飞书消息对象
        
    Returns:
        论文信息字典，包含 arxiv_id, title, title_zh, arxiv_url, relevance, novelty, abstract, first_author
    """
    content_str = message.get("body", {}).get("content", "")
    if not content_str:
        return None
    
    try:
        content = json.loads(content_str)
    except json.JSONDecodeError:
        return None
    
    paper_info = {}
    
    # 尝试解析 post 类型消息（直接有 content 字段）
    if "content" in content and isinstance(content.get("content"), list):
        paper_info = _parse_post_message(content)
    
    # 尝试解析富文本消息（有 zh_cn 包装）
    if not paper_info.get("arxiv_id"):
        zh_content = content.get("zh_cn", {})
        if zh_content:
            paper_info = _parse_post_message(zh_content)
    
    # 尝试解析卡片消息
    if not paper_info.get("arxiv_id"):
        paper_info = _parse_card_message(content)
    
    # 尝试从纯文本中解析
    if not paper_info.get("arxiv_id"):
        paper_info = _parse_plain_text(content_str)
    
    return paper_info if paper_info.get("arxiv_id") else None


def _parse_post_message(content: Dict) -> Dict:
    """解析 post 类型消息"""
    paper_info = {}
    
    content_lines = content.get("content", [])
    is_abstract_section = False
    abstract_lines = []
    
    for line in content_lines:
        for item in line:
            tag = item.get("tag", "")
            text = item.get("text", "")
            href = item.get("href", "")
            
            # 提取 ArXiv 链接
            if tag == "a" and "arxiv.org" in href:
                paper_info["arxiv_url"] = href
                arxiv_id = _extract_arxiv_id(href)
                if arxiv_id:
                    paper_info["arxiv_id"] = arxiv_id
            
            # 提取英文标题
            if text.startswith("论文题目:") or text.startswith("Title:"):
                title = re.sub(r"^(论文题目:|Title:)\s*", "", text).strip()
                paper_info["title"] = title
            
            # 提取中文翻译
            if text.startswith("中文翻译:") or text.startswith("中文标题:"):
                title_zh = re.sub(r"^(中文翻译:|中文标题:)\s*", "", text).strip()
                paper_info["title_zh"] = title_zh
            
            # 提取摘要
            if text == "论文摘要:" or text.startswith("论文摘要:"):
                is_abstract_section = True
                # 如果摘要在同一行
                abstract_text = text.replace("论文摘要:", "").strip()
                if abstract_text:
                    abstract_lines.append(abstract_text)
                continue
            
            if is_abstract_section:
                if text == "---" or text.startswith("作者信息:"):
                    is_abstract_section = False
                    if abstract_lines:
                        paper_info["abstract"] = "\n".join(abstract_lines).strip()
                elif text and text != "---":
                    abstract_lines.append(text)
            
            # 提取第一作者
            if "第一作者:" in text:
                match = re.search(r"第一作者:\s*([^,，]+)", text)
                if match:
                    paper_info["first_author"] = match.group(1).strip()
            
            # 提取评分 - 支持 [4/5] (8/10) 格式
            if "相关度:" in text or "Relevance:" in text:
                match = re.search(r"\((\d+)/10\)", text)
                if match:
                    paper_info["relevance"] = int(match.group(1))
            
            if "新颖度:" in text or "Novelty:" in text:
                match = re.search(r"\((\d+)/10\)", text)
                if match:
                    paper_info["novelty"] = int(match.group(1))
    
    # 如果摘要还在收集中
    if abstract_lines and "abstract" not in paper_info:
        paper_info["abstract"] = "\n".join(abstract_lines).strip()
    
    return paper_info


def _parse_card_message(content: Dict) -> Dict:
    """解析卡片消息"""
    paper_info = {}
    
    text_content = json.dumps(content, ensure_ascii=False)
    
    # 从整个内容中提取 ArXiv ID
    arxiv_id = _extract_arxiv_id(text_content)
    if arxiv_id:
        paper_info["arxiv_id"] = arxiv_id
        paper_info["arxiv_url"] = f"https://arxiv.org/abs/{arxiv_id}"
    
    return paper_info


def _parse_plain_text(content_str: str) -> Dict:
    """从纯文本中解析"""
    paper_info = {}
    
    # 提取 ArXiv ID
    arxiv_id = _extract_arxiv_id(content_str)
    if arxiv_id:
        paper_info["arxiv_id"] = arxiv_id
        paper_info["arxiv_url"] = f"https://arxiv.org/abs/{arxiv_id}"
    
    return paper_info


def _extract_arxiv_id(text: str) -> Optional[str]:
    """
    从文本中提取 ArXiv ID
    
    支持格式：
    - https://arxiv.org/abs/2603.12345
    - https://arxiv.org/pdf/2603.12345
    - arxiv:2603.12345
    - 2603.12345
    """
    patterns = [
        r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})",
        r"arxiv[:\s]+(\d{4}\.\d{4,5})",
        r"\b(\d{4}\.\d{4,5})\b"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def build_record_fields(paper_info: Dict, summary: str = "") -> Dict:
    """
    构建多维表格记录字段
    
    Args:
        paper_info: 论文信息字典
        summary: AI生成的摘要总结（可选）
        
    Returns:
        多维表格字段字典
    """
    arxiv_url = paper_info.get("arxiv_url", "")
    
    fields = {
        "论文题目": paper_info.get("title", ""),
        "中文翻译": paper_info.get("title_zh", ""),
        "论文摘要": summary if summary else paper_info.get("abstract", ""),
        "第一作者": paper_info.get("first_author", ""),
        "相关度": paper_info.get("relevance", 0),
        "新颖度": paper_info.get("novelty", 0),
        "收藏时间": int(datetime.now().timestamp() * 1000)
    }
    
    # 链接字段 - 超链接格式
    if arxiv_url:
        fields["链接"] = {
            "link": arxiv_url,
            "text": arxiv_url
        }
    
    return fields
