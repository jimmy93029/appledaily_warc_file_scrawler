import json
import pathlib

# Define base paths
TEXT_DIR = pathlib.Path("/mnt/data/appledaily")  # Holds article JSON files
IMAGE_METADATA_DIR = pathlib.Path("/mnt/data/images-metadata")  # Holds image metadata JSON files
IMAGE_METADATA_NAME = "/mnt/data/images-metadata"
OTHERS_DIR = TEXT_DIR / "others"  # Additional article JSON files
OUTPUT_FILE = "/mnt/data/text.json"  # Output file

# Collect all JSON article files
json_files = list(TEXT_DIR.glob("*/" * 4 + "*.json"))  # /year/month/day/new_id/new_id.json
json_files.extend(OTHERS_DIR.glob("*.json"))  # /others/*.json

print(f"🔍 Found {len(json_files)} articles. Processing...")

# Store all articles in a list
articles = []

# Process each article JSON file
for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract article fields
        article = {
            "id": data["altids"][0]["value"] if "altids" in data else file.stem,
            "uri": data.get("uri", ""),
            "firstcreated": data.get("firstcreated", ""),
            "headlines": data["headlines"][0]["value"] if "headlines" in data else "",
            "subjects": data.get("subjects", [{}])[0].get("name", ""),  # Get first subject name
            "bodies": data["bodies"][0]["value"] if "bodies" in data else "",
            "first_image": None,
            "other_images": [],
        }

        # Construct paths for image metadata
        article_rel_path = file.relative_to(TEXT_DIR).parent  # year/month/day/new_id

        # Extract images from associations (if available)
        if "associations" in data:
            images = [
                img["uri"].split("/")[-1] for img in data["associations"]
                if img["type"] == "picture" and "uri" in img
            ]

            if images:
                # Find metadata file for the first image (absolute path)
                first_img_metadata = IMAGE_METADATA_DIR / article_rel_path / "img" / f"{images[0]}.json"
                first_img_metadata_name = IMAGE_METADATA_NAME / article_rel_path / "img" / f"{images[0]}.json"

                if first_img_metadata.exists():
                    article["first_image"] = str(first_img_metadata_name)  # Store absolute path

                # Find metadata files for other images (absolute paths)
                article["other_images"] = [
                    str(IMAGE_METADATA_NAME / article_rel_path / "img" / f"{img}.json")
                    for img in images[1:]
                    if (IMAGE_METADATA_DIR / article_rel_path / "img" / f"{img}.json").exists()
                ]

        # Append to articles list
        articles.append(article)

    except Exception as e:
        print(f"❌ Error processing {file}: {e}")

# Save all articles to a single JSON file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=4, ensure_ascii=False)

print(f"✅ Saved {len(articles)} articles to {OUTPUT_FILE}")
