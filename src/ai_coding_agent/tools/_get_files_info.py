import os

from ._dataclasses import ToolResponse


def get_files_info(
    wd: str,
    directory: str = ".",
) -> ToolResponse:
    """Lists files in a specified directory relative to the working directory, providing file size and directory status

    Args:
        directory: Directory path to list files from, relative to the working directory (default is the working directory itself)

    Returns:
        A ToolResponse class instance with message content if has_error attribute is False, otherwise an error_message if has_error is True
    """
    try:
        abs = os.path.abspath(wd)
        norm_path = os.path.normpath(os.path.join(abs, directory))

        if os.path.commonpath([abs, norm_path]) != abs:
            return ToolResponse.error(
                f"Error: Cannot list {directory} as it is outside the permitted working directory"
            )

        op = []
        for item in os.listdir(norm_path):
            file_path = os.path.join(abs, directory, item)
            op.append(
                f"{item}: file_size={os.path.getsize(file_path)} bytes, is_dir={os.path.isdir(file_path)}"
            )

        return ToolResponse.success("\n".join(op))
    except Exception as e:
        return ToolResponse.error(f"Error occurred while getting file info: {e}")
