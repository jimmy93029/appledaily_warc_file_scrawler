from war2text import process_warc
from downloadfile import download
from utils import write_json, unique_data, clear_seen, get_folder_size
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
        timeon = time.time()
        asyncio.run(download(website, field, connect, dirrname))
        timeoff = time.time() 
        print(f"download interval = {interval}, connect = {connect} with time = {(timeoff - timeon)/60}")
        
        # read warc files 
        timeon = time.time()
        filenames = [os.path.join(dirrname, filename) for filename in os.listdir(dirrname)]              
        with multiprocessing.Pool() as pool:
            datas = pool.map(process_warc, filenames)
        
        writing_tasks = [(unique_data(datas[i], seen), filenames[i]) for i in range(len(datas))]   
        with multiprocessing.Pool() as pool:
            pool.starmap(write_json, writing_tasks)
        timeoff = time.time()
        
        print(f"processing file takes {(timeoff - timeon)/60}")
        seen = clear_seen(seen)
        subprocess.run(['rm', '-r', dirrname], check=True)
        times += interval


if __name__ == "__main__":
    dirr = os.path.join(os.getcwd(), "files")
    start = 681
    end = 803
    connect = 40
    interval = 6
    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    main(dirr, website, connect, start, end, interval)


