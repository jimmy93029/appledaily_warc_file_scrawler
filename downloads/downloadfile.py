import asyncio
import subprocess
import requests
from bs4 import BeautifulSoup


async def download_file(url, output_file, connect, files_dir):
     command = f"axel -a -n {connect} -o {files_dir} -q {url}"
     process = await asyncio.create_subprocess_exec(*command.split())
     await process.wait()


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


async def download(website, field, connect, files_dir):

    urls = geturls(website)
    output_files = [f'file{i}.warc' for i in range(field[1])]

    tasks = []

    for i in range(field[0], field[1]):
        task = asyncio.create_task(download_file(urls[i], output_files[i], connect, files_dir))
        tasks.append(task)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

"""    
if __name__ == "__main__":
    field = [0, 3]
    connect = 50
    website = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"
    asyncio.run(main(website, field, connect))
"""
