import asyncio
import gzip
import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin


DEFAULT_VIEWER_FALLBACK = (
    "https://web.archive.org/web/20250913223717id_/"
    "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
)

async def download_file(url, output_file, connect, files_dir):
    file_path = os.path.join(files_dir, output_file)
    file_path_st = file_path + ".st"

    # 1. 檢查是否已下載完成
    if os.path.exists(file_path) and not os.path.exists(file_path_st):
        return os.path.getsize(file_path) > 0

    # 2. 建立指令 (建議直接傳入 List，避免 split 報錯)
    # -a: 顯示進度條, -n: 連線數, -o: 輸出路徑, -q: 安靜模式
    cmd = ["axel", "-a", "-n", str(connect), "-o", file_path, "-q", url]

    try:
        # 3. 執行並獲取進程
        process = await asyncio.create_subprocess_exec(*cmd)

        # 4. 等待結束
        await process.wait()

        # 5. 檢查回傳碼 (重要！)
        if process.returncode == 0:
            print(f"✅ 下載完成: {output_file}")
            return os.path.exists(file_path) and os.path.getsize(file_path) > 0
        else:
            # 如果是 401 或是網路斷線，axel 會回傳非 0
            print(f"❌ 下載出錯: {output_file} (Error Code: {process.returncode})")
            return False
            # 這裡不拋出 Exception，交由外部的 check_st_files 偵測下載是否殘留

    except Exception as e:
        print(f"🚨 執行 axel 時發生系統錯誤: {e}")
        return False

def _viewer_urls(website):
    """Read one viewer page, including Wayback snapshots stored as gzip bytes."""
    response = requests.get(
        website,
        timeout=60,
        headers={"User-Agent": "appledaily-warc-converter/1.0"},
    )
    response.raise_for_status()
    body = response.content
    if body.startswith(b"\x1f\x8b"):
        body = gzip.decompress(body)
    text = body.decode(response.encoding or "utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")
    urls = []
    for link in soup.find_all("a"):
        label = link.get_text(strip=True)
        if re.search(
            r"www\.appledaily\.com\.tw-inf-20220903-015827-1bpf8-\d+\.warc(?:\.gz)?$",
            label,
        ):
            href = link.get("href")
            if href:
                urls.append(urljoin(website, href))
    return urls


def geturls(website, fallback_website=DEFAULT_VIEWER_FALLBACK):
    urls = []
    sources = [website]
    if fallback_website and fallback_website != website:
        sources.append(fallback_website)
    for source in sources:
        try:
            urls = _viewer_urls(source)
            if urls:
                if source != website:
                    print(f"即時 viewer 無法使用，改用保存的網址清單: {source}")
                break
            print(f"網址清單沒有 WARC 連結: {source}")
        except Exception as e:
            print(f"獲取網址清單出錯 ({source}): {e}")
    def warc_index(url):
        match = re.search(r"-(\d+)\.warc(?:\.gz)?(?:\?|$)", url)
        return int(match.group(1)) if match else 10**9
    return sorted(dict.fromkeys(urls), key=warc_index)

async def download(all_urls, field, connect, files_dir):
    tasks = []
    # 根據範圍建立下載任務
    for i in range(field[0], field[1]):
        url = all_urls[i]
        output_file = f'file{i}.warc'
        task = asyncio.create_task(download_file(url, output_file, connect, files_dir))
        tasks.append(task)

    # 等待這一批全部完成 (或超時/中斷)
    return await asyncio.gather(*tasks)
