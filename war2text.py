from fastwarc.warc import ArchiveIterator
from bs4 import BeautifulSoup
import re
from utils import meta_data, write_json, strip_ads


def extract_reporter(text):
    
    end = -1
    start = -1
    phrases = ["報導）","報導)"]
    for phrase in phrases:
        where = text.find(phrase, 0)
        end = where + 2 if where != -1 else end

    for i in range(end, 0, -1):
        if text[i] in ['（', '(']:
            start = i
            break
    
    oend = text.find('報導】', 0) + 2 
    ostart = -1
    for i in range(oend, 0, -1):
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
    for tag in soup.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr']):
        if tag == 'p':
            content += tag.get_text(strip=True) + '\n'
        elif tag == 'hr': 
            content += '\n'
        else:
            content += '\n' + tag.get_text(strip=True) + '\n'
    
    content, reporter = extract_reporter(content)
    return title, content, reporter


def has_chinese(text):
    # Chinese character range in Unicode
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    
    return bool(chinese_pattern.search(text))


def valid(content_type, target_url, status_code):
    
    if content_type and content_type.startswith('text/html'):
        if status_code == 200:
            if 'www.appledaily.com.tw' in target_url:
                return True
    return False


def process_warc(file_path):
    contents = []

    with open(file_path, 'rb') as file:

        warc_iter = ArchiveIterator(file, parse_http=True) 
        for record in warc_iter:
           
            if record.is_http and valid(record.http_content_type, record.headers['WARC-Target-URI'], record.http_headers.status_code):
                    
                encoding = record.http_charset or 'utf-8'
                html = record.reader.read().decode(encoding, errors='ignore')

                title, content, reporter = extract_text(html)
                content = strip_ads(content)

                if not has_chinese(content) or title == "":
                    continue
                contents.append(meta_data(title, content, reporter, record.record_date, record.headers['WARC-Target-URI']))
    return contents

file_path = "www.appledaily.com.tw-inf-20220903-015827-1bpf8-00802.warc.gz"
write_json(process_warc(file_path), "meta_802", "datas")

