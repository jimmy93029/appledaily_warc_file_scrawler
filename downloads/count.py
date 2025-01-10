import os
import json


def check_date(min_date, max_date, first):

    if first.isdigit() and int(first) > max_date:
        max_date = int(first)
    if first.isdigit() and int(first) < min_date:
        min_date = int(first)


def check_catagory(catagory, subject):
    
    if subject not in catagory:
        catagory[subject] = 1
    else:
        catagory[subject] += 1
    

def check_file(min_date, max_date, catagory):
    date = 0
    for dic in data:
        first = dic["firstcreated"].split('-')[0]
        
        if first.isdigit() and int(first) > max_date:
            max_date = int(first)
        if first.isdigit() and int(first) < min_date:
            min_date = int(first)
        
        subject = dic['subjects'][0]['name']
        if subject not in catagory:
            catagory[subject] = 1
        else:
            catagory[subject] += 1
    
    return min_date, max_date


dirr = os.path.join(os.getcwd(), "datastw")
cnt = 0
min_date = 2050
max_date = 0
catagory = {}

for name in os.listdir(dirr):
    path = os.path.join(dirr, name)
    if os.path.isfile(path):
        with open(path, 'r') as file:
            data = json.load(file)
            cnt += len(data)
            min_date, max_date = check_file(min_date, max_date, catagory)
            
print(f"data's cnt = {cnt} ")
print(f"min_date = {min_date}, max_date = {max_date}")
print(f"catagory = {catagory}")

