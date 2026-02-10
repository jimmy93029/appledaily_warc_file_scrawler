import re
import json
import time
import html as html_lib
import trafilatura
from bs4 import BeautifulSoup

# --- 原有的 Helper 保持不變 ---
def get_reporter(text):
    end = -1
    start = -1
    phrases = ["報導）","報導)"]
    for phrase in phrases:
        where = text.find(phrase, 0)
        end = where + 2 if where != -1 else end
    for i in range(end, 1, -1):
        if text[i] in ['（', '(']:
            start = i
            break
    oend = text.find('報導】', 0) + 2 
    ostart = -1
    for i in range(oend, 1, -1):
        if text[i] == "【":
            ostart = i
            break
    if end != -1:
        return text[0:start], text[start+1:end]
    elif oend > 1:
        return text[oend+1:len(text)], text[ostart+1:oend]
    else:
        return text, ""

def strip_ads(text):
    pos = -1
    phrases = ["《蘋果新聞網》", "「升級壹會員」", "《升級壹會員》"]
    for phrase in phrases:
        where = text.find(phrase, 0)
        pos = where if where != -1 else pos
    break_point = -1
    for i in range(pos, -1, -1):
        if text[i] == '\n':
            break_point = i
            break
    return text[0:break_point] if break_point != -1 else text

def valid_content(content):
    if not re.search(r'[\u4e00-\u9fff]+', content):
        return False
    if "抱歉，要找的頁面不存在" in content or "Sorry, page not found" in content:
        return False
    if len(content):
        return False
    return True

# --- 新版網域過濾機制 ---
def valid_url(content_type, target_url):
    if not content_type or not content_type.startswith('text/html'):
        return False
    url_lower = target_url.lower()
    if 'appledaily' not in url_lower:
        return False
    # 黑名單：搜尋、CDN、標籤頁
    blocklist = ['/search/', '/applesearch/', '/ak.', '.ak/', '/tag/']
    if any(b in url_lower for b in blocklist):
        return False
    # 層級深度檢查
    if len(target_url.split('/')) < 6:
        return False
    return True

# --- 新版預清洗邏輯 (地基整理) ---
def clean_raw_html_garbage(html_str):
    if not html_str: return ""
    # 移除 Hex Chunk 標記
    cleaned = re.sub(r'\s+[0-9a-fA-F]{4,8}\s+', '\n', html_str)
    cleaned = re.sub(r'00000000[\r\n\s]*$', '', cleaned)
    cleaned = re.sub(r'>[0-9a-fA-F]{4,8}<', '><', cleaned)
    return cleaned

# --- 修改後的核心提取函式 (雙引擎系統) ---
def extract_text(raw_html):
    """
    取代原本單一的 BS4 邏輯，改為：
    1. 預清洗
    2. Trafilatura 提取
    3. Meta Description 救援
    """
    # 1. 預清洗
    html_str = clean_raw_html_garbage(raw_html)
    
    # Engine B: Trafilatura (主引擎)
    try:
        tf_result = trafilatura.extract(html_str, output_format='json', no_fallback=False)
        if tf_result:
            res = json.loads(tf_result)
            tf_content = res.get('text', '')
            if tf_content.strip() and len(tf_content) > 50:
                content_cleaned, reporter = get_reporter(tf_content)
                return title, strip_ads(content_cleaned), reporter
    except:
        pass

    soup = None
    try:
        soup = BeautifulSoup(html_str, 'html.parser')
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ''
    except:
        return "", "", ""

    # Engine D: Meta Description (救援引擎)
    if soup:
        meta_desc = soup.find('meta', property='og:description') or \
                    soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            m_content = html_lib.unescape(meta_desc.get('content'))
            if len(m_content) > 50:
                content_cleaned, reporter = get_reporter(m_content)
                return title, strip_ads(content_cleaned), reporter

    return title, "", ""