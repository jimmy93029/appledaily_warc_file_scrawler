#!/bin/bash
set -euo pipefail

# Define paths
TEXT_JSON="/mnt/data/text.json"
TEXT_DB="/mnt/data/text.db"
IMAGE_METADATA_DIR="/mnt/data/images-metadata"

# Step 1: Build images-metadata if not exists
if [ ! -d "$IMAGE_METADATA_DIR" ]; then
    echo "📂 Creating images-metadata..."
    python3 build_img_metadata.py
else
    echo "✅ images-metadata already exists, skipping creation."
fi

# Step 2: Build text.json if not exists
if [ ! -f "$TEXT_JSON" ]; then
    echo "📂 Creating text.json..."
    python3 build_text_metadata.py
else
    echo "✅ text.json already exists, skipping creation."
fi

# Step 3: Build text.db from text.json
if [ ! -f "$TEXT_DB" ]; then
    echo "📂 Creating text.db from text.json..."
    python3 convert_json_to_db.py
else
    echo "✅ text.db already exists, skipping creation."
fi

# Step 4: Enable full-text search (FTS) on text.db
echo "🔍 Enabling full-text search (FTS) for text.db..."
sqlite-utils disable-fts "$TEXT_DB" news || echo "⚠️ Failed to disable FTS."
sqlite-utils enable-fts "$TEXT_DB" news headlines bodies --tokenize porter --create-triggers || echo "⚠️ Failed to enable FTS."

# Step 5: Check if FTS is working, if not, rebuild it
echo "🔍 Checking if FTS5 index is populated..."
FTS_COUNT=$(sqlite3 "$TEXT_DB" "SELECT count(*) FROM news_fts;" 2>/dev/null || echo "ERROR")
if [[ "$FTS_COUNT" == "ERROR" || "$FTS_COUNT" == "0" ]]; then
    echo "⚠️ FTS5 index is empty or not working. Rebuilding..."
    sqlite3 "$TEXT_DB" "INSERT INTO news_fts(news_fts) VALUES('rebuild');" || echo "❌ Failed to rebuild FTS index!"
else
    echo "✅ FTS5 index contains $FTS_COUNT entries."
fi

set -e
echo "🚀 Build completed successfully!"
