from fastwarc.warc import ArchiveIterator
from bs4 import BeautifulSoup
from utils_and_ninjs3 import get_url_img_id, get_new_id
import os
import re


def extract_image_info(html):
    image_info = {}
    soup = BeautifulSoup(html, 'html.parser')
    
    # 定義圖片附件的標準開頭 (用來自動過濾 UI 雜訊)
    IMG_PREFIX = "https://static-arc.appledaily.com.tw"

    # 直接掃描所有 <img> 標籤，這比只找 <figure> 更全面
    for img_tag in soup.find_all("img"):
        # 1. 處理內容路徑：優先順序 data-src -> data-original -> src
        img_uri = img_tag.get("data-src") or img_tag.get("data-original") or img_tag.get("src")
        
        # 2. 過濾邏輯：必須存在且符合指定的 Prefix
        if not img_uri or not img_uri.startswith(IMG_PREFIX):
            continue
            
        # 防止重複處理同一張圖
        if img_uri in image_info:
            continue

        # 3. 提取圖片說明文字 (Caption)
        caption_text = ""
        
        # 尋找最近的父層容器 (支援新舊版的 figure, div 或 p)
        parent = img_tag.find_parent(["figure", "div", "p"])
        if parent:
            # 搜尋可能的說明標籤，匹配 class 包含 image_text, caption, 或 text 的標籤
            cap_tag = parent.find(["figcaption", "div", "span"], class_=re.compile("image_text|caption|text"))
            if cap_tag:
                caption_text = cap_tag.get_text(strip=True)
        
        # 如果標籤層級找不到說明，回退使用 alt 或 title 屬性
        if not caption_text:
            caption_text = img_tag.get("alt", "").strip() or img_tag.get("title", "").strip()

        # 4. 依照 Ninjs 3 所需格式封裝
        image_info[img_uri] = {
            "img_id": get_url_img_id(img_uri),
            "img_name": caption_text,
            "img_uri": img_uri
        }

    return image_info

        
def valid_image(content_type, uri, images_in_text):

    if content_type and content_type.startswith('image/'):
        if uri.startswith("https://static-arc.appledaily.com.tw"):

            new_id = get_new_id(uri, "image")
            if new_id in images_in_text and uri in images_in_text[new_id]: 
                return True
    return False


def get_image_filename(uri, base_dir):

    # Extract the date (20210513 -> 2021/05/13)
    new_id = get_new_id(uri, "image")
    name = uri.split('/')[-1]
    
    # Construct the directory structure
    sub_path = f"{new_id}/img/{name}"    # Need to conform with metadata rendition format in ninjs3
    full_path = os.path.join(base_dir, sub_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    return full_path

