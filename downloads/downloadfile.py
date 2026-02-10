import asyncio
import requests
from bs4 import BeautifulSoup
import os

async def download_file(url, output_file, connect, files_dir):
    file_path = os.path.join(files_dir, output_file)
    file_path_st = file_path + ".st"

    # 檢查是否已下載完成
    if os.path.exists(file_path) and not os.path.exists(file_path_st):
        # 檔案完整，跳過
        return 

    # 使用 axel 進行斷點續傳
    command = f"axel -a -n {connect} -o {file_path} -q {url}"
    process = await asyncio.create_subprocess_exec(*command.split())
    await process.wait()
    print(f"下載狀態更新: {output_file}")

def geturls(website):
    urls = []
    try:
        response = requests.get(website, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                text = link.get_text(strip=True)
                if 'www.appledaily.com.tw-inf-20220903-015827-1bpf8-' in text:
                    urls.append(link.get('href'))
    except Exception as e:
        print(f"獲取網址清單出錯: {e}")
    return urls

async def download(all_urls, field, connect, files_dir):
    tasks = []
    # 根據範圍建立下載任務
    for i in range(field[0], field[1]):
        url = all_urls[i]
        output_file = f'file{i}.warc'
        task = asyncio.create_task(download_file(url, output_file, connect, files_dir))
        tasks.append(task)

    # 等待這一批全部完成 (或超時/中斷)
    await asyncio.gather(*tasks)