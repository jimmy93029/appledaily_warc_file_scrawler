import concurrent.futures
import subprocess
import requests
from bs4 import BeautifulSoup
import os


def download_file(url, connect, output_dir):
    try:
        command = ["axel", "-n", str(connect), "-o", str(output_dir), str(url)]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading {url}: {e}")


def geturls(website):

    urls = []
    response = requests.get(website)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a'):
            text = link.get_text(strip=True)

            if 'www.appledaily.com.tw-inf-20220903-015827-1bpf8-' in text:
                urls.append(link.get('href'))

    return urls


def download(website, field, connect, files_dir):

    urls = geturls(website)
    tasks = []

    for i in range(field[0], field[1]):
        tasks.append((urls[i], connect, files_dir))
    
    """
    for i in range(field[0], field[1]):
        download_file(urls[i], connect, files_dir)
    """

    
    num_processes = field[1] - field[0]
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        
        futures = [executor.submit(download_file, task) for task in tasks]
        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
    
    print("finish ?")


website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8" 
field = [222, 225]
connect = 10
files_dir = os.path.join(os.getcwd(),'files222')
download(website, field, connect, files_dir)

