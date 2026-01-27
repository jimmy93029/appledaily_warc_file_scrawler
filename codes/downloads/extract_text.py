from fastwarc.warc import ArchiveIterator
from bs4 import BeautifulSoup
import re


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


def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ''

    content = ''
    for article in soup.find_all("article"): 
        for tag in article.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr']):
            if tag == 'p':
                content += tag.get_text(strip=True) + '\n'
            elif tag == 'hr': 
                content += '\n'
            else:
                content += '\n' + tag.get_text(strip=True) + '\n'
    
    content, reporter = get_reporter(content)
    return title, strip_ads(content), reporter


def has_chinese(text):
    # Chinese character range in Unicode
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    
    return bool(chinese_pattern.search(text))


def valid_text(content_type, target_url):
    
    if content_type and content_type.startswith('text/html'):
        if 'www.appledaily.com.tw' in target_url and len(target_url.split('/')) >= 5:
            return True
    return False


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

    if break_point != -1:
        return text[0:break_point]
    else:
        return text


