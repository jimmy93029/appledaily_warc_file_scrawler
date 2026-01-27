from extract_warc2 import process_warc
from downloadfile import download
from utils_ninjs3 import write_json
import multiprocessing
import shutil
import asyncio
import time
import os


def main(dirr, json_dirr, output_base_dir, website, connect, start, end, interval, workers):
    
    times = start
    while times < end:
                
        field = [times, times + interval] if times + interval < end else [times, end]
        dirrname = dirr + str(times)
    
        if not os.path.exists(dirrname):
            os.mkdir(dirrname)
            print(f"mkdir {dirrname}")
        
        # 1. downlaod files until they are downlaod completely
        timeon = time.time()
        
        complete = False
        while not complete:
            asyncio.run(download(website, field, connect, dirrname))
            complete = check_st_files(dirrname)

        timeoff = time.time() 
        print(f"download interval = [{field[0]}, {field[1]}], connect = {connect} with time = {(timeoff - timeon)/60}")
        
        # 2. read warc files 
        timeon = time.time()
        filenames = [os.path.join(dirrname, filename) for filename in os.listdir(dirrname)] 
        args = [(file_path, output_base_dir) for file_path in filenames]             

        with multiprocessing.Pool(processes=interval, maxtasksperchild=workers) as pool:
            pool.starmap(process_warc, args)

        timeoff = time.time() 
        print(f"processing file takes {(timeoff - timeon)/60}")
        shutil.rmtree(dirrname)
        times += interval


def check_st_files(directory):
    """Check if there exists any file ending with .st in the directory."""
    for file in os.listdir(directory):  # Iterate over files in the directory
        if file.endswith(".st"):
            return False  # Found a .st file, return False immediately
    return True  # No .st file found, return True


if __name__ == "__main__":
    dirr = os.path.join(os.getcwd(), "files_current")
    json_dirr = os.path.join(os.getcwd(), "datastw")
    output_base_dir="/mnt/data/datastw"

    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    connect = 35
    start = 364
    end = 803
    interval = 7
    workers = 5

    main(dirr, json_dirr, output_base_dir, website, connect, start, end, interval, workers)


