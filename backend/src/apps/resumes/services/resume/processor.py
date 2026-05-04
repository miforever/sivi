"""
Resume processing utilities.
"""

import os


def process_uploaded_file(file_obj):
    """
    Process an uploaded resume file.

    Args:
        file_obj: Either a file object with name/size/content_type attributes or a file path string

    Returns:
        dict: Processed file information
    """
    # Handle both file objects and file paths
    if hasattr(file_obj, "read"):
        # It's a file object
        return {
            "filename": getattr(file_obj, "name", "uploaded_file"),
            "size": getattr(file_obj, "size", 0),
            "content_type": getattr(file_obj, "content_type", "application/octet-stream"),
            "processed": True,
            "message": "File processed successfully",
        }
    elif isinstance(file_obj, str) and os.path.isfile(file_obj):
        # It's a file path
        return {
            "filename": os.path.basename(file_obj),
            "size": os.path.getsize(file_obj),
            "content_type": "application/octet-stream",
            "processed": True,
            "message": "File processed successfully from path",
        }
    else:
        raise ValueError(f"Unsupported file object type: {type(file_obj)}")
