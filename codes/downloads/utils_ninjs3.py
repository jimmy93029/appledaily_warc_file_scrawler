import os
import json
import re
from datetime import datetime

GB = 1073741824

def write_json(data, output_dir, file_path):
    """Writes data as a JSON file in the specified output directory."""
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
    path = os.path.join(output_dir, f"{file_path}.json")

    with open(path, "w") as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)
    # print(f"write file = {file_path}")

def get_new_id(url, status):
    """Extracts an ID from the URL based on the type (image/text)."""
    parts = url.split('/')
    if status == "image" and len(parts) >= 5:
        return parts[4]
    elif status == "text" and len(parts) >= 6:
        return parts[5].split('?')[0] if '?' in parts[5] else parts[5]
    return None  # Return None if the structure is unexpected

def get_url_img_id(url):
    """Extracts image ID from a URL safely."""
    parts = url.split('/')
    return parts[6] if len(parts) > 6 else None  # Prevent IndexError


def meta_data(title, content, reporter, warc_date, uri, image_names, image_ids, image_uris):
    """Generates metadata JSON conforming to ninjs 3.0 format."""
    standard = {
        "name": "ninjs",
        "version": "3.0",
        "schema": "https://www.iptc.org/std/ninjs/ninjs-schema_3.0.json"
    }

    # Ensure warc_date is a datetime object
    if not isinstance(warc_date, datetime):
        warc_date = datetime.strptime(warc_date, "%Y-%m-%d")  # Adjust format if needed

    # Extract and format `firstcreated`
    acdate = uri.split('/')[4] if len(uri.split('/')) >= 5 else "unknown"
    firstcreated = f"{acdate[:4]}-{acdate[4:6]}-{acdate[6:]}" if acdate.isdigit() else "unknown"

    versioncreated = warc_date.strftime("%Y-%m-%d")
    contentcreated = datetime.now().strftime("%Y-%m-%d")  # Current timestamp
    language = "zh-Hant-TW"
    type_ = "text"

    headlines = [{"role": "main", "value": title}]
    subjects = [{"name": uri.split('/')[3] if len(uri.split('/')) >= 4 else "unknown"}]

    bodies = [{"role": "main", "contentType": "text/plain", "value": content}]

    # Extract reporter and location details
    reporter_parts = re.split('[／/]', reporter)
    by = reporter_parts[0] if reporter_parts else "unknown"
    located = reporter_parts[1] if len(reporter_parts) > 1 else ""

    altid = uri.split('/')[5] if len(uri.split('/')) >= 6 else ""
    altids = [{"role": "internal", "value": altid}]

    # Ensure image_names, image_ids, and image_uris have the same length
    if not (len(image_names) == len(image_ids) == len(image_uris)):
        raise ValueError("image_names, image_ids, and image_uris must have the same length")

    # Creating associations with renditions
    associations = [
        {
            "name": f"picture{i}",  # Dynamic naming: picture0, picture1, picture2, etc.
            "uri": image_uris[i],  # Provided image URI
            "type": "picture",
            "headlines": [
                {"value": image_names[i]}  # Image title
            ],
            "renditions": [
                {
                    "href": f"./{altid}/img/{image_ids[i]}.jpg",  # Uses image ID instead of name
                    "contentType": "image/jpg"
                }
            ]
        } for i in range(len(image_names))
    ]

    return {
        "uri": uri,
        "standard": standard,
        "firstcreated": firstcreated,
        "versioncreated": versioncreated,
        "contentcreated": contentcreated,
        "type": type_,
        "language": language,
        "headlines": headlines,
        "subjects": subjects,
        "bodies": bodies,
        "associations": associations,
        "by": by,
        "located": located,
        "altids": altids
    }