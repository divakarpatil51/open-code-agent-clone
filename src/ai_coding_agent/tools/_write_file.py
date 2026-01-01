from ai_coding_agent.tools._dataclasses import ToolResponse
import os


def write_file(wd: str, file_path: str, content: str) -> ToolResponse:
    """Write content to file present at given working directory and file path.
    Args:
        file_path: File path to which content needs to be written
        content: data to be written

    Returns:
        A ToolResponse class instance with message content if has_error attribute is False, otherwise an error_message if has_error is True
    """
    try:
        abs = os.path.abspath(wd)
        norm_path = os.path.normpath(os.path.join(abs, file_path))

        if os.path.commonpath([abs, norm_path]) != abs:
            return ToolResponse.error(
                f"Error: Cannot write to {file_path} as it is outside the permitted working directory"
            )

        if not os.path.isfile(norm_path):
            return ToolResponse.error(
                f"Error: File not found or is not a regular file: {norm_path}"
            )

        with open(norm_path, mode="w") as f:
            f.write(content)

        return ToolResponse.success(f"Successfully wrote to {file_path}")

    except Exception as e:
        return ToolResponse.error(f"Error occurred while writing to file: {e}")
