from war2text import process_warc
from downloadfile import download
from utils import write_json, unique_data, get_folder_size
import multiprocessing
import subprocess
import asyncio
import time
import os


def main(dirr, website, connect, start, end, interval):
    
    times = start
    seen = {}
    while times < end:
                
        field = [times, times + interval] if times + interval < end else [times, end]
        dirrname = dirr + str(times)
       
        if not os.path.exists(dirrname):
            os.mkdir(dirrname)
            print(f"mkdir {dirrname}")
        
        # downlaod files until they are downlaod completely
        start = time.time()
        asyncio.run(download(website, field, connect, dirrname))
        previous_size = get_folder_size(dirrname)
        
        """
        while True:
            time.sleep(60)
            current_size = get_folder_size(dirrname)

            if previous_size == current_size:
                print("download complete")
                break
            else:
                print("still downloading")
        """
        end = time.time() 
        print(f"download interval = {interval}, connect = {connect} with time = {(end - start)/60}")
        
        # read warc file 
        print("start reading warc file")
        
        filenames = [os.path.join(dirrname, filename) for filename in os.listdir(dirrname)]        
        
        with multiprocessing.Pool() as pool:
            datas = pool.map(process_warc, filenames)
        
        unique_datas = [[unique_data(data[1], seen), data[0]] for data in datas]
        
        with multiprocessing.Pool() as pool:
            pool.map(write_json, unique_datas)
        
        subprocess.run(['rm', '-r', dirrname], check=True)
        times += interval


if __name__ == "__main__":
    dirr = os.path.join(os.getcwd(), "files")
    start = 226
    end = 803
    connect = 10
    interval = 5
    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    main(dirr, website, connect, start, end, interval)


