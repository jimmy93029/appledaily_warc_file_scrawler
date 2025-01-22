import sqlite_utils
import glob
import json

db = sqlite_utils.Database("mydatabase.db")

# Iterate through all JSON files in the directory
for json_file in glob.glob("*.json"):
    table_name = json_file.replace(".json", "")  # Use file name as table name
    with open(json_file, "r") as f:
        db[table_name].insert_all(json.load(f), pk="id")  # Use 'id' as primary key

print("All JSON files have been imported into mydatabase.db")
