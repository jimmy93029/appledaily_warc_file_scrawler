from fastwarc.warc import ArchiveIterator
from bs4 import BeautifulSoup
import re


def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ''

    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag.get('content') if description_tag else ''

    content = ''
    for tag in soup.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr']):
        if tag == 'p':
            content += tag.get_text(strip=True) + '\n'
        elif tag == 'hr': 
            content += '\n'
        else:
            content += '\n' + tag.get_text(strip=True) + '\n'
    
    return title, description, content


def extract_reporter(content):

    end = 0
    for i in range(len(content), -1, -1):
        if i - 2 >= 0 and content[i-2:i+1] in ["報導）","報導)"]:
            end = i
            break
    
    start = 0
    for i in range(end, 0, -1): 
        if content[i] in ['（', '(']:
            start = i
            break
    
    if end > start:
        return content[0:start], content[start+1:end]
    
    return content, ""


def has_chinese(text):
    # Chinese character range in Unicode
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')

    # Check if the pattern is present in the text
    return bool(chinese_pattern.search(text))


def process_warc(file_path):
    contents = []

    with open(file_path, 'rb') as file:

        warc_iter = ArchiveIterator(file, parse_http=True)
        
        for record in warc_iter:
            
            if record.http_content_type and record.http_content_type.startswith('text/html'):
                status_code = record.http_headers.status_code
                target_url = record.headers['WARC-Target-URI']
                
                if status_code == 200 and 'appledaily' in target_url:
                    
                    encoding = record.http_charset or 'utf-8'
                    html = record.reader.read().decode(encoding, errors='ignore')

                    title, description, content = extract_text(html)
                    content, reporter = extract_reporter(content)

                    if content == "" or content == "\n\n\n\n" or title == "":
                        continue
                    contents.append({"title": title, 'description': description, 'content': content, 'reporter': reporter})
    return contents

