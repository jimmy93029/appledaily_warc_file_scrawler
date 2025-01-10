import os
import json
import re
from datetime import datetime


GB = 1073741824 


def write_json(data, file_path, output_dir):
    
    name = os.path.basename(file_path)

    with open(f'{output_dir}/apple_{name}.json', 'w') as json_file:
        json.dump(data, json_file, indent=2)
    print(name)


def clear_seen(seen):
    if seen.__sizeof__() > 26 * GB:
        seen = {}
    return seen


def unique_data(data, seen):
    new_data = []
    if data == None:
        return new_data

    for dic in data:
        title = dic['headlines'][0]['value']
        subject = dic['subjects'][0]['name']
        if seen != None and title not in seen and title != "" and subject != "video":
            seen[title] = 1
            new_data.append(dic)

    return new_data


def strip_ads(text):
    
    pos = -1
    phrases = [ "《蘋果新聞網》","「升級壹會員」", "《升級壹會員》"]
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


def meta_data(title, content, reporter, warc_date, target_url):
    
    uri = target_url
    standard = {
                'name':'ninjs',
                'version':'2.1',
                'schema':"https://iptc.org/std/ninjs/ninjs-schema_2.1.json"    
    }
    acdate = target_url.split('/')[4]
    firstcreated = f"{acdate[0:4]}-{acdate[4:6]}-{acdate[6:len(acdate)]}"
    versioncreated = warc_date.date().strftime("%Y-%m-%d")
    contentcreated = datetime.now().date().strftime("%Y-%m-%d")
    language = "zh-Hant-TW"
    type_ = "text"
    headlines = [{
            "role" : "main",
            "value": title
    }]
    subjects = [{
        "name":target_url.split('/')[3]
    }]
    bodies = [{
        "role":"main",
        "value": content
    }]
    by = re.split('[／/]', reporter)[0]
    located = re.split('[／/]', reporter)[1] if len(re.split('[／/]', reporter)) > 1 else ""
    altids = [{
        "role":"internal",
        "value":target_url.split('/')[5] if len(target_url.split('/')) >= 6 else ""
        }]

    return {"uri":uri,
            "standard":standard,
            "firstcreated":firstcreated,
            "versioncreated":versioncreated,
            "contentcreated":contentcreated,
            "type":type_,
            "language":language,
            "headlines":headlines,
            "subjects":subjects,
            "bodies":bodies,
            "by":by,
            "located":located,
            "altids":altids
            }


