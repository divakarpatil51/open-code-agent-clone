import os

from ._dataclasses import ToolResponse

READ_SIZE = 10000


def get_file_content(
    wd: str,
    file_path: str,
) -> ToolResponse:
    """Get file contents for a file path relative to the working directory
    Args:
        file_path: Path of the file for which to get file contents

    Returns:
        A ToolResponse class instance with message content if has_error attribute is False, otherwise an error_message if has_error is True
    """
    try:
        abs = os.path.abspath(wd)
        norm_path = os.path.normpath(os.path.join(abs, file_path))

        if os.path.commonpath([abs, norm_path]) != abs:
            return ToolResponse.error(
                f"Error: Cannot list {file_path} as it is outside the permitted working directory"
            )

        if not os.path.isfile(norm_path):
            return ToolResponse.error(
                f"Error: File not found or is not a regular file: {norm_path}"
            )

        with open(norm_path, mode="r") as f:
            content = f.read(READ_SIZE)
            if f.read(1):
                content += (
                    f"\n.... File {file_path} truncated at {READ_SIZE} characters"
                )

        return ToolResponse.success(content)
    except Exception as e:
        return ToolResponse.error(f"Error occurred while retrieving file contents: {e}")
