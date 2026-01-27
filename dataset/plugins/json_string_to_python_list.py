import json
from datasette import hookimpl

def json_string_to_list(json_string):
    """Convert a JSON string into a Python list."""
    if not json_string:
        return []  # Return an empty list if input is None or empty
    try:
        return json.loads(json_string)  # Convert JSON string to list
    except json.JSONDecodeError:
        return []  # Return an empty list if JSON is malformed

@hookimpl
def extra_template_vars():
    """Registers functions for use in Jinja2 templates."""
    print("work !!")
    return {
        "json_string_to_list": json_string_to_list  # Makes function available in templates
    }
