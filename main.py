from war2text import process_warc
from downloadfile import download
from utils import write_json, unique_data, get_folder_size
import json
import asyncio
import subprocess
import time
import os


def main(dirr, website, connect, start, end, interval):
    
    times = start
    while times < end:
                
        seen = {}
        field = [times, times + interval] if times + interval < end else [times, end]
        dirrname = dirr + str(times)
       
        if not os.path.exists(dirrname):
            os.mkdir(dirrname)
            print(f"mkdir {dirrname}")
        
        # downlaod files until they are downlaod completely
        start = time.time()
        asyncio.run(download(website, field, connect, dirrname))
        previous_size = get_folder_size(dirrname)

        while True:
            time.sleep(60)
            current_size = get_folder_size(dirrname)

            if previous_size == current_size:
                print("download complete")
                break
            else:
                print("still downloading")
        end = time.time() 
        print(f"download interval = {interval}, connect = {connect} with time = {(end - start)/60}")
        # read warc file 
        print("start reading warc file")
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
    connect = 15
    interval = 4
    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    main(dirr, website, connect, start, end, interval)


