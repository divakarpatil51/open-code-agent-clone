import os


def get_files_info(wd: str, directory: str = "."):
    """Lists files in a specified directory relative to the working directory, providing file size and directory status

    Args:
        directory: Directory path to list files from, relative to the working directory (default is the working directory itself)

    Returns:
        File details
    """
    try:
        abs = os.path.abspath(wd)
        norm_path = os.path.normpath(os.path.join(abs, directory))

        if os.path.commonpath([abs, norm_path]) != abs:
            return f"Error: Cannot list {directory} as it is outside the permitted working directory"

        op = []
        for item in os.listdir(norm_path):
            file_path = os.path.join(abs, directory, item)
            op.append(
                f"{item}: file_size={os.path.getsize(file_path)} bytes, is_dir={os.path.isdir(file_path)}"
            )

        return "\n".join(op)
    except Exception as e:
        return f"Error occurred while getting file info: {e}"
