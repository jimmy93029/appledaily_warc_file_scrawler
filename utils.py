import os
import json


GB = 1073741824 


def write_json(data, code):

    output_dir = "datas"
    with open(f'{output_dir}/apple_{code}.json', 'w') as json_file:
        json.dump(data, json_file, indent=2)


def clear_seen(seen):
    if seen.__sizeof__() > 26 * GB:
        seen = {}


def unique_data(data, seen):
    new_data = []
    if data == None:
        return new_data

    for dic in data:
        if seen != None and dic['title'] not in seen and dic['title'] != "":
            seen[dic['title']] = 1
            new_data.append(dic)

    clear_seen(seen)

    return new_data


def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    return total_size
