import os
import json
from datetime import datetime
from fastwarc import ArchiveIterator
from extract_text import valid_url, extract_text, valid_content
from extract_image2 import valid_image, extract_image_info, get_image_filename
from utils_and_ninjs3 import get_new_id, meta_data, write_json, decode_response_content


def process_warc(file_path, output_base_dir="/mnt/data/datastw"):
    news = {}
    images_in_text = {}

    dirr = os.path.join(output_base_dir, os.path.splitext(os.path.basename(file_path))[0])
    os.makedirs(dirr, exist_ok=True)
    print(f"Processing: {file_path}")

    # Step 1. Extract text from news
    with open(file_path, 'rb') as file:
        warc_iter = ArchiveIterator(file, parse_http=True)
        for record in warc_iter:
            # 關鍵修正：只處理 Response 類型的紀錄
            if record.headers.get('WARC-Type') != 'response':
                continue

            uri = record.headers.get('WARC-Target-URI', "")
            if not uri: continue

            if record.is_http and record.http_headers and "200 OK" in (record.http_headers.status_line or ""):
                content_type = record.http_headers.get('Content-Type', None)
        
                if valid_url(content_type, uri):
                    try:
                        new_id = get_new_id(uri, "text")
                            
                        # 使用新版解碼邏輯
                        clean_bytes = decode_response_content(record, uri)
                        encoding = record.http_charset or 'utf-8'
                        html = clean_bytes.decode(encoding, errors='replace')

                        # 使用新版 Hybrid 提取邏輯
                        title, content, reporter = extract_text(html)
                        
                        if not valid_content(content) or not title:
                            continue

                        # 圖片提取依然基於清洗後的 HTML
                        image_info = extract_image_info(html)

                        warc_date = record.headers.get('WARC-Date', None)
                        warc_date = datetime.strptime(warc_date, "%Y-%m-%dT%H:%M:%SZ") if warc_date else datetime.now()

                        news[new_id] = {
                            "title": title,
                            "content": content,
                            "reporter": reporter,
                            "warc-date": warc_date.strftime("%Y-%m-%d"),
                            "uri": uri,
                            "image_info": []
                        }
                        images_in_text[new_id] = image_info
                    except Exception as e:
                        print(f"Error processing {uri}: {e}")
                        continue

    # Step 2. Extract images from news
    with open(file_path, 'rb') as stream:
        for record in ArchiveIterator(stream, parse_http=True):
            uri = record.headers.get('WARC-Target-URI', "")
            if not uri:
                continue
            
            if record.is_http:
                Content_type = record.http_headers.get('Content-Type', None)
                
                if valid_image(Content_type, uri, images_in_text):

                    new_id = get_new_id(uri, "image")
                    image_path = get_image_filename(uri, dirr)

                    with open(image_path, 'wb') as image_file:
                        image_file.write(record.reader.read())

                    # Ensure new_id exists in `news` before modifying
                    if new_id in news and new_id in images_in_text and uri in images_in_text[new_id]:
                        news[new_id]["image_info"].append(images_in_text[new_id][uri])

    # Step 3. Write news into JSON files
    for new_id, new in news.items():
        json_data = meta_data(
            new["title"], new["content"], new["reporter"],
            datetime.strptime(new["warc-date"], "%Y-%m-%d"),  # Convert back to datetime object
            new["uri"], 
            [img["img_name"] for img in new["image_info"]], 
            [img["img_id"] for img in new["image_info"]],
            [img["img_uri"] for img in new["image_info"]]
        )

        # Use the existing `new_id` instead of recalculating it
        write_json(json_data, f"{dirr}/{new_id}", new_id)
    
    print(f"finish writing {file_path}")
