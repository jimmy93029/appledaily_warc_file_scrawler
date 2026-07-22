# downloads_new2

`downloads_new/` 的隔離修正版。原目錄不會被修改。

## 已整合

- 嚴格處理 HTTP chunked、gzip、deflate 與 charset。
- 修正 Trafilatura 成功路徑中 `title` 尚未定義的錯誤。
- Trafilatura 回傳非空但無效的正文、或引擎拋出例外時，繼續嘗試
  `<article>` 與 meta-description；只有通過正文驗證才停止 fallback。
- 文章 hostname 接受 `appledaily.com`、`appledaily.com.tw` 及其真正
  子網域（包括 `tw.appledaily.com`）。文章 path 的末端必須是完整的 26
  字元 article ID；中間的來源日期片段即使不是 8 位數也不會淘汰文章。
  不使用容易誤收偽造網址的單純 `"appledaily" in URL`。
- 不使用 `except: pass`；traceback 與每個 WARC 的 summary 都寫入主控台／nohup log。
- 直接輸出 ninjs 3.2 `standard` 宣告。
- `firstCreated` 依序採用 `NewsArticle.datePublished`、
  `article:published_time`、`VideoObject.uploadDate`、主文第一個
  `.timestamp`、`time[datetime]`、主文第一個 `<time>` 日期；全部缺少時
  才使用 URL 的 `YYYYMMDD` 並補為台灣時間 `T00:00:00+08:00`。
- 使用程式產出 JSON 的當下台灣時間填入 `contentCreated`。
- 使用 `WARC-Date` 填入 `versionCreated`，並統一轉成 `+08:00`。
- HTML 日期必須包含時間與時區；只有合法的 URL `YYYYMMDD` 日期可補為
  台灣時間午夜，沒有 URL 日期時不猜測。
- 移除文章 `uri` 的 query parameters 與 fragment，方便去重。
- article ID 只從 URL path 取得；`?utm_*`、fragment、percent-encoded
  尾端空白不會成為 ID 的一部分。
- 輸出前清理文字欄位中的 Mojibake、HTML entities、BOM、零寬/軟連字符與異常控制字元。
- Mojibake 使用 `ftfy.fix_encoding()` 修復 UTF-8 被誤以 Latin-1/CP1252 解讀的亂碼。
- 不自動移除長數字或十六進位字串；檢查報告顯示多數可能是電話、案號或正文中的合法資訊。
- 支援署名分隔符 `／ / ╱ ∕ ⁄` 與非地點規則。
- 圖片保留規則：URL 含 article ID，或出現在 OG / JSON-LD。
- 支援 `src`、`data-src`、`data-original`、`srcset`、`data-srcset`。
- 以反向索引處理 URL 不含 article ID 的 S3/外部圖片。
- caption 排除空值、Banner、純數字等 placeholder。
- 有圖片時輸出 `type: composite` 與 `profile: text-photo`；無圖片時輸出 `type: text`。
- 圖片 association 遵循專案指定格式，只含原始 URI 與可用 caption，不輸出 `renditions`。
- 正文保留原始署名行，同時另外產生 `by` 與 `located`。
- 使用官方 camelCase：`firstCreated`、`contentCreated`、`versionCreated`、`altIds`。
- 不輸出 `genres`、`infoSources`、`imageCreator`。

完整的新舊欄位差異見 [`NINJS_FORMAT_DIFF.md`](NINJS_FORMAT_DIFF.md)。

## 先測試單一 WARC

不要直接寫入既有 `/mnt/data/appledaily2`。先由操作者建立新的輸出根目錄；
程式不會自行建立最上層 output：

```bash
mkdir -p /mnt/data/appledaily2_new

PYTHONPATH=venv/codes/downloads_new2 \
venv/bin/python venv/codes/downloads_new2/extract_warc2.py \
  /mnt/data/venv/codes/downloads/files_current364/file364.warc \
  --output /mnt/data/appledaily2_new
```

小範圍 smoke test：

```bash
PYTHONPATH=venv/codes/downloads_new2 \
venv/bin/python venv/codes/downloads_new2/extract_warc2.py \
  /mnt/data/venv/codes/downloads/files_current364/file364.warc \
  --output /tmp/downloads_new2_smoke \
  --max-records 2000
```

WARC 會直接輸出到日期樹，不建立 `fileN/`：

```text
appledaily2_new/
└── 2020/09/01/ARTICLE_ID/
    ├── ARTICLE_ID.json
    └── img/
```

## 給老師檢查：WARC 0 與 1

先由操作者建立獨立測試目錄，不會寫入既有的 `appledaily2` 或
`appledaily3`：

```bash
mkdir -p /mnt/data/working3/appledaily_teacher_test_0_1
```

再以 `--start 0 --end 2` 處理索引 0、1（`end` 是 exclusive）：

```bash
nohup /home/jimmywu/sinica/venv/bin/python -u \
  /home/jimmywu/sinica/venv/gitspace/downloads/main.py \
  --start 0 --end 2 --connect 5 \
  --output /mnt/data/working3/appledaily_teacher_test_0_1 \
  > /mnt/data/working3/appledaily_teacher_test_0_1.log 2>&1 &
```

每次只下載一個 WARC 到 output root，處理成功後立即刪除；轉換結果直接位於
`appledaily_teacher_test_0_1/YEAR/MONTH/DAY/ARTICLE_ID/`。

日期目錄依序採用正常 URL 日期、HTML／URL fallback 的 `firstCreated`；兩者都無法
提供合法日期時，才以 WARC 的 `versionCreated` 擷取日作為目錄 fallback，並在
summary 計數。WARC fallback 不會被寫成文章的 `firstCreated`。

## 下載並批次處理

程式會先讀取即時 ArchiveBot viewer；若該站無法連線，會自動改讀 Wayback
Machine 保存的同一個 job 頁面，再使用頁面中的 Internet Archive 直接連結。

先跑小批次，不要直接從 0 跑到 803：

```bash
PYTHONPATH=venv/codes/downloads_new2 \
venv/bin/python venv/codes/downloads_new2/main.py \
  --start 364 --end 366 \
  --connect 5 \
  --output /mnt/data/appledaily2_new
```

建議在 `tmux` 中執行，避免 SSH 中斷終止程序。

## 檢查結果

nohup log 中每個 WARC 的 JSON summary 會列出：

- 候選與唯一文章數
- 重複 response 數
- 保留圖片候選數
- 成功保存與未匹配圖片數
- 文章、圖片、寫檔錯誤數

只有 summary 沒有 fatal/write error 時，`main.py` 才會刪除該 WARC；失敗時保留
單一 WARC 供重跑，不會產生 `files_currentN/` 目錄。全域 duplicate 記錄寫在
output 旁邊的 `OUTPUT_NAME_duplicates.tsv`，不污染年份目錄。

## 日期整理與全域去重

實際典藏共有 804 個一般 shard，名稱是 `file0` 到 `file803`；另有一個不列入
編號的 `meta.warc.gz`。新版 `main.py` 在每篇 ninjs 產生後就直接使用
`YEAR/MONTH/DAY/ARTICLE_ID` 當作磁碟上的去重索引，不需要再執行第二階段。

`organize_deduplicate.py` 只保留給舊的 `fileN/ARTICLE_ID/` 資料樹轉換使用：

```bash
mkdir -p /mnt/data/appledaily3_deduplicated
python organize_deduplicate.py \
  /mnt/data/appledaily3 \
  /mnt/data/appledaily3_deduplicated
```

程式**不會建立最上層 output 目錄**。若該目錄不存在或無寫入權限，會在
讀取任何 shard 前顯示 `HUMAN ACTION REQUIRED`、建議的 `mkdir` 指令並停止。
由 programmer 確認及建立 output 後，程式才會在裡面自動建立年月日與文章
子目錄。

新版 `main.py` 與舊資料轉換器的輸出結構相同：

```text
appledaily3_deduplicated/
└── 2020/09/01/ARTICLE_ID/
    ├── ARTICLE_ID.json
    └── img/
```

相同日期與 article ID 再次出現時視為 duplicate。程式優先保留較新的
`versionCreated`；相同時依正文長度、圖片數及 shard 編號做固定排序。
duplicate 與 error TSV 放在資料樹旁邊，不會污染年份目錄。中斷後可加
`--resume` 繼續。
