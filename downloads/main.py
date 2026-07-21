#!/usr/bin/env python3
"""Download one ArchiveBot WARC at a time into a de-duplicated date tree."""

from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

from downloadfile import DEFAULT_VIEWER_FALLBACK, download, geturls
from extract_warc2 import process_warc


DEFAULT_WEBSITE = "https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8"


def warc_complete(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0 and not Path(f"{path}.st").exists()


def main(
    temp_prefix: str,
    output: str,
    website: str,
    fallback_website: str,
    connect: int,
    start: int,
    end: int,
    interval: int,
    workers: int,
    retries: int,
) -> int:
    output_root = Path(output).resolve()
    if not output_root.exists():
        print(
            "HUMAN ACTION REQUIRED: output directory does not exist.\n"
            "No download was started. Create it yourself, then rerun:\n"
            f"  mkdir -p {output_root}"
        )
        return 2
    if not output_root.is_dir():
        print(f"Output is not a directory: {output_root}")
        return 2
    if temp_prefix:
        print("提示: --temp-prefix 已停用；WARC 會逐檔下載到 output root，成功後立即刪除。")
    if interval != 1 or workers != 1:
        print("提示: 日期樹的全域去重採順序寫入；--interval/--workers 目前固定視為 1。")

    print("正在獲取完整網址清單...")
    all_urls = geturls(website, fallback_website)
    if not all_urls:
        print("無法獲取網址，結束程式。")
        return 2
    if end > len(all_urls):
        raise ValueError(f"end={end} exceeds available URL count {len(all_urls)}")

    for index in range(start, end):
        warc_path = output_root / f"file{index}.warc"
        completed = False
        for attempt in range(1, retries + 1):
            started = time.time()
            results = asyncio.run(download(all_urls, [index, index + 1], connect, str(output_root)))
            completed = all(results) and warc_complete(warc_path)
            print(
                f"下載 file{index} attempt={attempt} "
                f"completed={completed} elapsed={(time.time() - started) / 60:.2f}m"
            )
            if completed:
                break
            time.sleep(min(attempt * 30, 300))
            all_urls = geturls(website, fallback_website) or all_urls
        if not completed:
            print(f"file{index} 下載失敗；保留未完成檔案供續傳，不進行處理。")
            return 2

        started = time.time()
        summary = process_warc(str(warc_path), str(output_root))
        fatal = (
            summary.get("fatal_first_pass_errors", 0)
            or summary.get("fatal_second_pass_errors", 0)
            or summary.get("write_errors", 0)
        )
        print(f"處理 file{index} 耗時: {(time.time() - started) / 60:.2f} 分鐘")
        if fatal:
            print(f"file{index} 處理發生錯誤；保留 {warc_path} 以便重跑。")
            return 2
        warc_path.unlink()
        partial = Path(f"{warc_path}.st")
        if partial.exists():
            partial.unlink()
        print(f"file{index} 已寫入日期樹；刪除暫存 WARC: {warc_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temp-prefix", default="", help="deprecated; retained for old commands")
    parser.add_argument("--output", default="/mnt/data/datastw2")
    parser.add_argument("--website", default=DEFAULT_WEBSITE)
    parser.add_argument("--fallback-website", default=DEFAULT_VIEWER_FALLBACK)
    parser.add_argument("--connect", type=int, default=5)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=804)
    parser.add_argument("--interval", type=int, default=1, help="deprecated; processing is sequential")
    parser.add_argument("--workers", type=int, default=1, help="deprecated; processing is sequential")
    parser.add_argument("--retries", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main(**vars(parse_args())))
