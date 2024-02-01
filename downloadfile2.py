import concurrent.futures
import subprocess
import requests
from bs4 import BeautifulSoup


def download_file(url, connect, output_dir):
    command = ["axel", "-n", str(connect), "-o", str(output_dir), str(url)]
    subprocess.run(command)


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
 
    num_processes = field[1] - field[0]

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        
        futures = [executor.submit(download_file, task) for task in tasks]
        concurrent.futures.wait(futures)




