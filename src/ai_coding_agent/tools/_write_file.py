import os


def write_file(wd: str, file_path: str, content: str):
    """Write content to file present at given working directory and file path."""
    """
    Args:
        file_path: File path to which content needs to be written
        content: data to be written

    Returns:
        Success or error message
    """
    try:
        abs = os.path.abspath(wd)
        norm_path = os.path.normpath(os.path.join(abs, file_path))

        if os.path.commonpath([abs, norm_path]) != abs:
            return f"Error: Cannot write to {file_path} as it is outside the permitted working directory"

        if not os.path.isfile(norm_path):
            return f"Error: File not found or is not a regular file: {norm_path}"

        with open(norm_path, mode="w") as f:
            f.write(content)

        return f"Succcessfully wrote to {file_path}"

    except Exception as e:
        return f"Error occurred while writing to file: {e}"
