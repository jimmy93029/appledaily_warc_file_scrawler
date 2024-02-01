from war2text import process_warc
from downloadfile2 import download
from utils import write_json, unique_data, get_folder_size
import json
import asyncio
import subprocess
import os


def main(dirr, website, connect, start, end, interval):
    
    times = start
    while times < end:
                
        seen = {}
        field = [times, times + interval] if times + interval < end else [times, end]
        dirrname = dirr + str(times)
        
        if not os.path.exists(dirrname):
            os.mkdir(dirrname)

        # downlaod files until they are downlaod completely
        download(website, field, connect, dirrname)
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

        # read warc file 
        for filename in os.listdir(dirrname):
            file_path = os.path.join(dirrname, filename)

            if os.path.isfile(file_path):
                data = process_warc(file_path)
                data = unique_data(data, seen)
                write_json(data, filename)
                print(file_path)

        subprocess.run(['rm', '-r', dirrname], check=True)
        times += interval


if __name__ == "__main__":
    dirr = os.path.join(os.getcwd(), "files")
    start = 222
    end = 803
    connect = 10
    interval = 8
    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    main(dirr, website, connect, start, end, interval)


