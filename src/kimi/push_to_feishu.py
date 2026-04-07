"""
Code to render the output.json into a format suitable for Feishu (Lark), and to push it using Feishu Bot API.
"""
import json
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union
import re

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file (for local development)
load_dotenv()

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
OUTPUT_DIR = PROJECT_ROOT / "out"


def get_deepseek_client() -> OpenAI | None:
    """Create DeepSeek client if key exists."""
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_key:
        return None
    return OpenAI(
        api_key=deepseek_key,
        base_url="https://api.deepseek.com",
    )


def _extract_json_object(text: str) -> Dict:
    """Extract JSON object from model output."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    json_text = match.group(0)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        # Repair common bad escapes from LLM outputs.
        # Handle invalid escape sequences like \_ \- \. \( \) etc.
        repaired = re.sub(r"\\(?![\"\\\/bfnrtu])", r"\\\\", json_text)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            # More aggressive fix: remove all invalid backslash escapes
            # Keep only valid JSON escapes: \" \\ \/ \b \f \n \r \t \uXXXX
            def fix_escapes(s: str) -> str:
                result = []
                i = 0
                while i < len(s):
                    if s[i] == '\\' and i + 1 < len(s):
                        next_char = s[i + 1]
                        if next_char in '"\\/bfnrt':
                            result.append(s[i:i+2])
                            i += 2
                        elif next_char == 'u' and i + 5 < len(s):
                            # Unicode escape \uXXXX
                            result.append(s[i:i+6])
                            i += 6
                        else:
                            # Invalid escape - just keep the character without backslash
                            result.append(next_char)
                            i += 2
                    else:
                        result.append(s[i])
                        i += 1
                return ''.join(result)
            
            fixed = fix_escapes(json_text)
            return json.loads(fixed)


def _load_translate_prompt() -> str:
    """Load translation system prompt from configs/translate.md."""
    prompt_path = CONFIGS_DIR / "translate.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return ""


def translate_with_deepseek(paper_entry: Dict, deepseek_client: OpenAI) -> Dict:
    """Translate paper using DeepSeek API (OpenAI-compatible)."""
    title = paper_entry["title"]
    abstract = paper_entry["abstract"]
    authors = paper_entry["authors"]
    first_author = authors[0] if authors else "Unknown"
    corresponding_author = authors[-1] if authors else "Unknown"

    system_prompt = _load_translate_prompt()

    user_prompt = f"""请将下面论文信息翻译为中文，并输出严格 JSON（不要 markdown 代码块）：
{{
  "title_zh": "中文标题",
  "abstract_zh": "中文摘要（简洁、准确，建议120-220字）",
  "keywords_zh": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"]
}}

论文标题：{title}
论文摘要：{abstract[:3000]}
"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    completion = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=1200,
        temperature=0.0,
        messages=messages,
    )
    out_text = completion.choices[0].message.content.strip()
    translated = _extract_json_object(out_text)
    keywords = translated.get("keywords_zh", [])
    if not isinstance(keywords, list) or len(keywords) == 0:
        keywords = ["未生成关键词"]

    return {
        "title_zh": translated.get("title_zh", "（未翻译）"),
        "abstract_zh": translated.get("abstract_zh", "（未翻译）"),
        "keywords_zh": keywords[:5],
        "first_author": first_author,
        "corresponding_author": corresponding_author,
    }


def translate_paper_to_zh(paper_entry: Dict, deepseek_client: OpenAI | None = None) -> Dict:
    """Translate title/abstract and generate Chinese keywords using DeepSeek."""
    title = paper_entry["title"]
    abstract = paper_entry["abstract"]
    authors = paper_entry["authors"]
    first_author = authors[0] if authors else "Unknown"
    corresponding_author = authors[-1] if authors else "Unknown"

    # Try DeepSeek
    if deepseek_client is not None:
        return translate_with_deepseek(paper_entry, deepseek_client)

    # Fallback (no translation)
    return {
        "title_zh": "（未翻译）",
        "abstract_zh": abstract[:200] + ("..." if len(abstract) > 200 else ""),
        "keywords_zh": ["未生成关键词"],
        "first_author": first_author,
        "corresponding_author": corresponding_author,
    }


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """Get tenant_access_token from Feishu API."""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    body = {"app_id": app_id, "app_secret": app_secret}

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != 0:
        raise ValueError(f"Failed to get token: {data}")

    return data["tenant_access_token"]


def send_message(
    token: str,
    receive_id: str,
    content: Dict,
    msg_type: str = "interactive",
    reply_in_thread: bool = False,
    parent_message_id: str = None,
) -> str:
    """Send message via Feishu Bot API.

    Args:
        token: tenant_access_token
        receive_id: chat_id or open_chat_id
        content: message content dict
        msg_type: message type (interactive, text, etc.)
        reply_in_thread: whether to reply in thread
        parent_message_id: parent message id for thread reply

    Returns:
        message_id of the sent message
    """
    if reply_in_thread and parent_message_id:
        url = "https://open.feishu.cn/open-apis/im/v1/messages/reply"
        params = {}
        body = {
            "content": json.dumps(content),
            "msg_type": msg_type,
            "reply_in_thread": True,
            "message_id": parent_message_id,
        }
    else:
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": "chat_id"}
        body = {
            "receive_id": receive_id,
            "content": json.dumps(content),
            "msg_type": msg_type,
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, params=params, json=body)
    if response.status_code != 200:
        print(f"Error response: {response.status_code}")
        print(f"Response body: {response.text}")
        print(f"Request body: {json.dumps(body, indent=2, ensure_ascii=False)[:500]}")
    response.raise_for_status()
    data = response.json()

    if data.get("code") != 0:
        raise ValueError(f"Failed to send message: {data}")

    return data["data"]["message_id"]


def score_to_emoji_stars(paper_entry: Dict) -> str:
    """Convert score to 1-5 stars with emoji."""
    relevance = int(paper_entry.get("RELEVANCE", 0))
    novelty = int(paper_entry.get("NOVELTY", 0))
    star_count = max(1, min(5, round((relevance + novelty) / 4)))
    return f"[{star_count}/5]"


def render_paper_post_content(paper_entry: Dict, counter: int, translated: Dict) -> Dict:
    """Render a single paper as a Feishu post rich text message."""
    arxiv_id = paper_entry["arxiv_id"]
    title_en = paper_entry["title"]
    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
    keywords = "，".join(translated["keywords_zh"])

    # Get individual scores with stars (5 stars = 10 points, so 2 points per star)
    relevance = int(paper_entry.get("RELEVANCE", 0))
    novelty = int(paper_entry.get("NOVELTY", 0))
    rel_filled = (relevance + 1) // 2  # Convert 1-10 to 1-5
    nov_filled = (novelty + 1) // 2
    rel_stars = f"[{rel_filled}/5]"
    nov_stars = f"[{nov_filled}/5]"

    # Truncate abstract if too long
    abstract = translated['abstract_zh']
    if len(abstract) > 250:
        abstract = abstract[:250] + "..."

    return {
        "zh_cn": {
            "title": f"论文 {counter}: {translated['title_zh'][:35]}",
            "content": [
                [{"tag": "text", "text": f"论文题目: {title_en}"}],
                [{"tag": "text", "text": f"中文翻译: {translated['title_zh']}", "style": ["bold"]}],
                [{"tag": "text", "text": "---"}],
                [{"tag": "text", "text": "论文摘要:", "style": ["bold"]}],
                [{"tag": "text", "text": abstract}],
                [{"tag": "text", "text": "---"}],
                [{"tag": "text", "text": "作者信息:", "style": ["bold"]}],
                [{"tag": "text", "text": f"第一作者: {translated['first_author']}, 通讯作者: {translated['corresponding_author']}"}],
                [{"tag": "text", "text": "---"}],
                [{"tag": "text", "text": "关键词:", "style": ["bold"]}],
                [{"tag": "text", "text": keywords}],
                [{"tag": "text", "text": "---"}],
                [{"tag": "text", "text": "评分:", "style": ["bold"]}],
                [{"tag": "text", "text": f"相关度: {rel_stars} ({relevance}/10)"}],
                [{"tag": "text", "text": f"新颖度: {nov_stars} ({novelty}/10)"}],
                [{"tag": "a", "text": "点击查看 ArXiv 原文", "href": arxiv_url}],
            ],
        }
    }

def build_main_post_content(paper_count: int, title_list: List[str]) -> Dict:
    """Build the main Feishu post message with summary and top papers."""
    today = datetime.today().strftime("%Y-%m-%d")

    content_rows = [
        [{"tag": "text", "text": "ArXiv 每日论文速递", "style": ["bold"]}],
        [{"tag": "text", "text": f"日期: {today}"}],
        [{"tag": "text", "text": f"共筛选出 {paper_count} 篇相关论文"}],
        [{"tag": "text", "text": "---"}],
        [{"tag": "text", "text": "Top 论文预览:", "style": ["bold"]}],
    ]
    for title in title_list[:15]:
        content_rows.append([{"tag": "text", "text": title}])
    if len(title_list) > 15:
        content_rows.append([{"tag": "text", "text": f"... 以及另外 {len(title_list) - 15} 篇论文"}])

    return {
        "zh_cn": {
            "title": f"ArXiv Paper Alert - {today}",
            "content": content_rows,
        }
    }


def push_to_feishu(papers_dict: Dict, chat_id: str = None):
    """Push papers to Feishu chat.

    Args:
        papers_dict: dict of paper entries
        chat_id: Feishu chat ID (if None, uses FEISHU_CHAT_ID env var)
    """
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    if chat_id is None:
        chat_id = os.environ.get("FEISHU_CHAT_ID")

    if not app_id or not app_secret:
        print("Warning: FEISHU_APP_ID or FEISHU_APP_SECRET not set - not pushing to Feishu")
        return

    if not chat_id:
        print("Warning: FEISHU_CHAT_ID not set - not pushing to Feishu")
        return

    if len(papers_dict) == 0:
        return

    # Get access token
    token = get_tenant_access_token(app_id, app_secret)

    # Use DeepSeek for translation
    deepseek_client = get_deepseek_client()
    
    if deepseek_client is not None:
        print("Using DeepSeek for translation")
    else:
        print("Warning: DEEPSEEK_API_KEY not set - sending untranslated Chinese fields fallback")

    # Prepare paper lists/messages
    title_list = []
    paper_posts = []

    for i, (paper_id, paper) in enumerate(papers_dict.items(), 1):
        translated = translate_paper_to_zh(paper, deepseek_client)
        score_preview = score_to_emoji_stars(paper)
        title_list.append(f"{i}. {translated['title_zh']} {score_preview}")
        paper_posts.append(render_paper_post_content(paper, i, translated))

    # Send main post message
    main_post = build_main_post_content(len(papers_dict), title_list)
    main_msg_id = send_message(token, chat_id, main_post, msg_type="post")
    print(f"Main message sent: {main_msg_id}")

    # Send detailed papers as separate post messages (max 5 to avoid rate limits and cost)
    for i, post_content in enumerate(paper_posts[:5]):
        try:
            msg_id = send_message(token, chat_id, post_content, msg_type="post")
            print(f"Paper {i+1} message sent: {msg_id}")
        except Exception as e:
            print(f"Failed to send paper {i+1}: {e}")


if __name__ == "__main__":
    # Test with existing output.json
    with open(OUTPUT_DIR / "output.json", "r") as f:
        output = json.load(f)

    push_to_feishu(output)
