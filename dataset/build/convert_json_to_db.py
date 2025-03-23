import json
import sqlite3

TEXT_JSON = "/mnt/data/text.json"
TEXT_DB = "/mnt/data/text.db"

# 連接 SQLite
conn = sqlite3.connect(TEXT_DB)
cursor = conn.cursor()

# 創建正確的 news 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS news (
    id TEXT PRIMARY KEY,
    uri TEXT,
    firstcreated TEXT,
    headlines TEXT,
    subjects TEXT,
    bodies TEXT,
    first_image TEXT,
    other_images TEXT
);
""")

# 讀取 JSON 並插入數據
with open(TEXT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

news_data = [
    (
        item["id"], item["uri"], item["firstcreated"], item["headlines"],
        item["subjects"], item["bodies"], item["first_image"],
        json.dumps(item["other_images"])  # 存成 JSON 字串
    )
    for item in data
]

cursor.executemany("""
INSERT INTO news (id, uri, firstcreated, headlines, subjects, bodies, first_image, other_images)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", news_data)

conn.commit()
conn.close()
print("✅ Successfully converted text.json to text.db")
