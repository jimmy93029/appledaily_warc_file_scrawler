# 台灣《蘋果日報》網站典藏資料集產製工具

本 repository 將 ArchiveBot 保存的台灣《蘋果日報》WARC 網頁典藏轉換為可供研究使用的新聞文字、metadata 與圖片資料。目前 converter 輸出以 **ninjs 3.2** 為基礎的 project profile，並以 Git tags 保存 V1、V2 與 V3 程式歷史。

> [!IMPORTANT]
> 完整資料集尚無已驗證的公開下載網址、正式 licence、publisher 或 dataset PID。新聞文字與圖片可受著作權、隱私與研究倫理規範；使用或重新散布前請先確認權利與適用條件。

## Dataset at a glance

| Item | Value |
| --- | --- |
| Source | [ArchiveBot job `202209030158271bpf8`](https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8) |
| Coverage | 2003–2022 |
| Language tag | Traditional Chinese (`zh-Hant-TW`)；程式統一指定，未逐筆偵測 |
| Current code | V3 / `dataset-v3` / `4acdaa1` |
| Current output | ninjs 3.2 JSON and archived images |
| Layout | `YEAR/MONTH/DAY/ARTICLE_ID/` |
| Archive inventory | 804 numbered WARC shards (`00000`–`00803`) plus `meta.warc.gz` |

本資料由網頁典藏重新解析，並非從《蘋果日報》原始資料庫匯出。典藏 coverage、網站版型、擷取、清理及去重規則都可能影響最終結果，因此不應宣稱資料完整涵蓋所有歷史新聞。

## Documentation

完整的英文 dataset datasheet 以物件化方式分層維護：

- **Documentation index:** [documentation/main.md](documentation/main.md)
- [Description](documentation/description.md)
- [Supported applications](documentation/applications.md)
- [Distribution and licensing](documentation/distribution.md)
- [Composition, fields, and statistics](documentation/composition.md)
- [Collection and processing](documentation/collection-process.md)
- [Versioning and maintenance](documentation/lifecycle.md)
- [Responsible use, ethics, and limitations](documentation/responsible-use.md)

欄位狀態明確區分為 `VERIFIED`、`PARTIAL`、`UNKNOWN`、`NOT APPLICABLE`、`DEFERRED (>30 min)` 與 `HUMAN DECISION REQUIRED`。

## Repository layout

```text
.
├── documentation/   # Dataset datasheet and responsible-use documentation
├── downloads/       # WARC download, extraction, cleaning, and deduplication
├── smoke-test/      # Pipeline tests, diagnostics, and archive audits
└── dataset/         # Optional Datasette/SQLite presentation tooling
```

技術細節請參閱 [downloads/README.md](downloads/README.md)；ninjs 新舊格式差異見 [downloads/NINJS_FORMAT_DIFF.md](downloads/NINJS_FORMAT_DIFF.md)；測試與 audit 說明見 [smoke-test/README.md](smoke-test/README.md)。

## Requirements

已驗證的本機環境為 Ubuntu 22.04、Python 3.10、FastWARC 0.3.2、Beautiful Soup 4.12.3、Trafilatura 2.0.0、ftfy 6.3.1 與 requests 2.31.0。下載 WARC 另需 `axel`。

Repository 目前尚無 downloads pipeline 的完整 lock file；可以已驗證版本建立環境：

```bash
python3 -m venv .venv
.venv/bin/pip install \
  FastWARC==0.3.2 beautifulsoup4==4.12.3 requests==2.31.0 \
  trafilatura==2.0.0 ftfy==6.3.1
```

## Quick start

請先由操作者建立全新的 output root，再用少量 WARC shards 測試：

```bash
mkdir -p /mnt/data/appledaily_v3_new

PYTHONPATH=downloads .venv/bin/python downloads/main.py \
  --start 0 --end 2 \
  --connect 5 \
  --output /mnt/data/appledaily_v3_new
```

`--end` 為 exclusive；上述指令處理 shards 0 與 1。全量處理需 `--start 0 --end 804`，會耗時很久並使用大量儲存空間，請先確認輸出路徑、容量、log 與斷點策略。

## Versions

| Dataset | Git reference | Summary |
| --- | --- | --- |
| V1 | `dataset-v1` / `f747ffd` | 2024 text extraction and advertising cleanup |
| V2 | `dataset-v2` / `da0438d` | Image and Datasette/SQLite tooling expansion |
| V3 | `dataset-v3` / `4acdaa1` | Current WARC decoding, date recovery, image association, ninjs 3.2, and deduplication |

```bash
git checkout dataset-v3
```

`master` 持續更新，不一定等同歷史資料集產製時的程式。重現或引用特定版本時，請同時記錄 tag 與 commit。

## Citation and licence status

本 repository 尚無 `LICENSE`、`CITATION.cff` 或已核准的 dataset citation。在 publisher、licence、release version、下載 URL 與 PID 確定前，請勿虛構 DOI 或授權條款。

引用程式碼時至少請標明 repository、tag、commit 與存取日期：

```text
jimmy93029/appledaily_warc_file_scrawler,
dataset-v3, commit 4acdaa1, accessed YYYY-MM-DD.
```
