import json
import pathlib
import glob
from PIL import Image

# Define paths
IMAGE_DIRS = [
    "/mnt/data/appledaily/*/*/*/*/img/*.jpg",  # Standard directory
    "/mnt/data/appledaily/others/*/img/*.jpg"  # Others directory
]
IMAGE_METADATA_DIR = pathlib.Path("/mnt/data/images-metadata")  # Metadata storage

print(" Processing images...")

# Process each image
for pattern in IMAGE_DIRS:
    for img_path in glob.glob(pattern, recursive=True):
        img_path = pathlib.Path(img_path)
        try:
            with Image.open(img_path) as img:
                width, height = img.size

            # Determine JSON storage location
            article_dir = img_path.parents[1]  # year/month/day/new_id
            article_json_path = article_dir / f"{article_dir.name}.json"

            new_id, alt_text = "", ""

            # Retrieve new_id and alt_text from the article JSON
            if article_json_path.exists():
                with open(article_json_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                # Take new_id
                if "altids" in metadata and metadata["altids"]:
                    new_id = metadata["altids"][0]["value"]

                # Take alt_text
                for assoc in metadata.get("associations", []):
                    if "uri" in assoc and img_path.name in assoc["uri"]:
                        alt_text = assoc["headlines"][0]["value"]

            # Create metadata JSON filename
            metadata_file = IMAGE_METADATA_DIR / img_path.relative_to("/mnt/data/appledaily")
            metadata_file = metadata_file.with_suffix(".jpg.json")

            # Ensure directories exist
            metadata_file.parent.mkdir(parents=True, exist_ok=True)

            # Save metadata to a JSON file
            metadata = {
                "id": img_path.stem,
                "new_id": new_id,
                "width": width,
                "height": height,
                "alt_text": alt_text,
                "location": str(img_path)  # Absolute path to the actual image
            }
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Error processing {img_path}: {e}")

print("🎉 Image metadata stored in `images-metadata` successfully!")
