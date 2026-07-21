import os
import shutil
import asyncio
import time
import multiprocessing
from extract_warc2 import process_warc
from downloadfile import download_file, geturls

# ==========================================
# 救援偵測邏輯
# ==========================================

def get_missing_indices(output_base_dir, start, end):
    """
    掃描輸出目錄，找出編號連續性中缺失的索引。
    """
    missing = []
    print(f"🔍 正在掃描 {output_base_dir} (範圍: {start} - {end-1})...")
    
    for i in range(start, end):
        folder_path = os.path.join(output_base_dir, f"file{i}")
        
        # 判定缺失：資料夾不存在，或是資料夾內沒有任何檔案
        if not os.path.exists(folder_path):
            missing.append(i)
        elif not os.listdir(folder_path):
            missing.append(i)
            
    if missing:
        print(f"📊 掃描完成：共計 {end - start} 個任務，其中 {len(missing)} 個缺失。")
        print(f"缺失清單片段: {missing[:10]} ...")
    else:
        print("🎉 恭喜！所有資料夾均已完整。")
    return missing

async def download_specific_list(all_urls, indices, connect, files_dir):
    """
    僅下載清單中指定的特定 WARC 檔案。
    """
    tasks = []
    for idx in indices:
        if idx >= len(all_urls):
            print(f"⚠️ 索引 {idx} 超出 URL 清單長度，跳過。")
            continue
        url = all_urls[idx]
        output_file = f'file{idx}.warc'
        tasks.append(download_file(url, output_file, connect, files_dir))
    
    if tasks:
        await asyncio.gather(*tasks)

def check_st_files(directory):
    """ 檢查目錄下是否還有 axel 留下的 .st 狀態檔 """
    if not os.path.exists(directory):
        return True
    for file in os.listdir(directory):
        if file.endswith(".st"):
            return False
    return True

# ==========================================
# 救援執行主流程
# ==========================================

def run_correction(temp_dir, output_base_dir, website, connect, start, end, interval, workers):
    # 0. 獲取初始 URL 清單
    all_urls = geturls(website)
    if not all_urls:
        print("❌ 無法獲取網址，請檢查網路或網址是否有效。")
        return

    # 1. 找出需要補救的編號
    missing_indices = get_missing_indices(output_base_dir, start, end)
    if not missing_indices:
        return

    # 2. 分批處理缺失的索引
    for i in range(0, len(missing_indices), interval):
        current_batch = missing_indices[i : i + interval]
        batch_label = f"{current_batch[0]}-{current_batch[-1]}"
        dirrname = os.path.join(temp_dir, f"fix_{batch_label}")

        if not os.path.exists(dirrname):
            os.makedirs(dirrname, exist_ok=True)

        print(f"\n🛠️  開始處理補救批次: {current_batch}")
        
        # 下載邏輯 (含失敗重試與防封鎖機制)
        complete = False
        retry_count = 0
        
        while not complete:
            # 執行下載
            asyncio.run(download_specific_list(all_urls, current_batch, connect, dirrname))
            
            # 檢查是否下載成功 (無 .st 檔)
            complete = check_st_files(dirrname)
            
            if not complete:
                retry_count += 1
                # 判斷是否為 URL 過期或是被封鎖 (401)
                # 採取指數退避等待：30s, 60s, 120s... 最大 5 分鐘
                wait_time = min(retry_count * 30, 300)
                print(f"⚠️  批次 {batch_label} 有檔案未完成。")
                
                if retry_count >= 2:
                    print(f"🔄 偵測到多次失敗，嘗試重新獲取 URL 清單並冷卻 {wait_time} 秒...")
                    all_urls = geturls(website) # 刷新網址，應對 Session 過期
                
                time.sleep(wait_time)
                
                if retry_count > 5:
                    print(f"🛑 批次 {batch_label} 重試次數過多，跳過此批次，請檢查伺服器狀態。")
                    break

        # 處理 WARC (只有在下載完成後才執行)
        if complete:
            filenames = [os.path.join(dirrname, f) for f in os.listdir(dirrname) if f.endswith(".warc")]
            if not filenames:
                print(f"❓ 找不到 WARC 檔案，批次 {batch_label} 可能下載失敗。")
            else:
                args = [(file_path, output_base_dir) for file_path in filenames]
                with multiprocessing.Pool(processes=len(filenames), maxtasksperchild=workers) as pool:
                    pool.starmap(process_warc, args)
                print(f"✅ 批次 {batch_label} 處理完成。")

        # 清理暫存並強制冷卻
        if os.path.exists(dirrname):
            shutil.rmtree(dirrname)
        
        # 批次間的固定休息，保護伺服器
        print(f"💤 批次間冷卻中...")
        time.sleep(15)

if __name__ == "__main__":
    # 配置參數 (建議調低 connect 避免 401)
    CONFIG = {
        "temp_dir": os.path.join(os.getcwd(), "fix_temp"),
        "output_base_dir": "/mnt/data/datastw2",
        "website": "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8",
        "connect": 5,      # 降低連線數 (原 15 太激進，容易觸發 401)
        "start": 0,
        "end": 803,
        "interval": 2,     # 縮小批次，一次處理 2 個更穩定
        "workers": 2
    }

    run_correction(**CONFIG)