from war2text import process_warc
from downloadfile import download
from utils import write_json, unique_data, get_folder_size
import json
import asyncio
import os


def main(dirr, website, connect):
    
    times = 0
    while times < 175:
                
        seen = {}
        field = [times, times + 35] if times + 35 < 175 else [times, 175]
        dirrname = dirr + str(times)
        
        if not os.path.exists(dirrname):
            os.mkdir(dirrname)

        asyncio.run(download(website, field, connect, dirrname))
        previous_size = get_folder_size(dirrname)

        while True:
            current_size = get_folder_size(dirrname)

            if current_size == previous_size:
                print("Download completed.")
                break
            else:
                print("Still downloading...")
                previous_size = current_size
                time.sleep(60)  

        for filename in os.listdir(dirrname):
            file_path = os.path.join(dirrname, filename)

            if os.path.isfile(file_path):
                data = process_warc(file_path)
                data = unique_data(data, seen)
                write_json(data, filename)
                print(file_path)

        times += 30


if __name__ == "__main__":
    dirr = os.getcwd() + "/files"
    connect = 50
    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    main(dirr, website, connect)


