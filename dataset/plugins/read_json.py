import json
from pathlib import Path
from datasette import hookimpl


def read_image_metadata(metadata_path):
    """ Reads metadata from a given image metadata JSON file. """
    if not metadata_path:
        print("❌ Metadata path is empty")
        return None  # No image metadata available

    metadata_file = Path(metadata_path)
    if not metadata_file.exists():
        print(f"❌ Metadata file does not exist: {metadata_path}")
        return None  # File does not exist

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ Metadata loaded: {data}")
            return {
                "location": data.get("location", ""),
                "width": data.get("width", 0),
                "height": data.get("height", 0),
                "alt_text": data.get("alt_text", "")
            }
    except Exception as e:
        print(f"❌ Error reading image metadata {metadata_path}: {e}")
        return None


@hookimpl
def extra_template_vars():
    """ Registers functions for use in Jinja2 templates. """
    return {
        "read_image_metadata": read_image_metadata  # Now templates can use this function
    }
