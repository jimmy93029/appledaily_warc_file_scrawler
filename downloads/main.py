from extract_warc2 import process_warc
from downloadfile import download, geturls
import multiprocessing
import shutil
import asyncio
import time
import os


def main(dirr, output_base_dir, website, connect, start, end, interval, workers):
    # 0. 預先抓取所有網址 (優化：只抓一次)
    print("正在獲取完整網址清單...")
    all_urls = geturls(website)
    if not all_urls:
        print("無法獲取網址，結束程式。")
        return

    times = start
    while times < end:
        current_batch_end = min(times + interval, end)
        field = [times, current_batch_end]
        dirrname = dirr + str(times)
    
        if not os.path.exists(dirrname):
            os.makedirs(dirrname, exist_ok=True)
            print(f"mkdir {dirrname}")
        
        # 1. 下載批次檔案直到完全成功 (Axel 會產生 .st 檔)
        timeon = time.time()
        complete = False
        while not complete:
            # 傳入已抓好的 all_urls
            asyncio.run(download(all_urls, field, connect, dirrname))
            complete = check_st_files(dirrname)

        timeoff = time.time() 
        print(f"下載批次 [{field[0]}, {field[1]}] 完成，耗時: {(timeoff - timeon)/60:.2f} 分鐘")
        
        # 2. 處理批次 WARC 檔案
        timeon = time.time()
        # 確保只抓取 .warc 檔案且排除沒下載完的殘骸
        filenames = [os.path.join(dirrname, f) for f in os.listdir(dirrname) if f.endswith(".warc")] 
        args = [(file_path, output_base_dir) for file_path in filenames]             

        # 使用 Pool 進行併行處理
        with multiprocessing.Pool(processes=interval, maxtasksperchild=workers) as pool:
            pool.starmap(process_warc, args)

        timeoff = time.time() 
        print(f"處理批次完成，耗時: {(timeoff - timeon)/60:.2f} 分鐘")
        
        # 3. 清理目錄，進入下一輪
        shutil.rmtree(dirrname)
        times += interval

def check_st_files(directory):
    for file in os.listdir(directory):
        if file.endswith(".st"):
            return False
    return True

if __name__ == "__main__":
    # 配置
    dirr = os.path.join(os.getcwd(), "files_current")
    output_base_dir = "/mnt/data/datastw"
    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    
    connect = 35
    start = 0
    end = 803
    interval = 7
    workers = 5 # maxtasksperchild: 子進程跑幾次任務後重啟

    main(dirr, output_base_dir, website, connect, start, end, interval, workers)