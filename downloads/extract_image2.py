from fastwarc.warc import ArchiveIterator
from bs4 import BeautifulSoup
from utils_ninjs3 import get_url_img_id, get_new_id
import os


def extract_image_info(html):
    image_info = {}
    soup = BeautifulSoup(html, 'html.parser')

    # Loop through all <figure> tags (without class restriction)
    for figure in soup.find_all("figure"):
        img_tag = figure.find("img")

        if not img_tag:
            continue

        # Extract the image URL
        img_uri = img_tag.get("src")

        # Save image data
        if not img_uri or not img_uri.startswith("https://static-arc.appledaily.com.tw/"):
            continue

        # Move to the parent div that contains both <figure> and the caption
        parent_div = figure.find_parent("div")
        caption_tag = parent_div.find("div", class_="image_text") if parent_div else None
        caption_text = caption_tag.text.strip() if caption_tag else img_tag.get("alt", "").strip()

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

