import os

READ_SIZE = 10000

def get_file_content(wd: str, file_path: str) -> str:
    """Get file contents for a file path relative to a working directory"""
    """
    Args:
        file_path: Path of the file for which to get file contents

    Returns:
        File contents
    """
    try:
        abs = os.path.abspath(wd)
        norm_path = os.path.normpath(os.path.join(abs, file_path))

        if os.path.commonpath([abs, norm_path]) != abs:
            return f"Error: Cannot list {file_path} as it is outside the permitted working directory"

        if not os.path.isfile(norm_path):
            return f"Error: File not found or is not a regular file: {norm_path}"

        with open(norm_path, mode="r") as f:
            content = f.read(READ_SIZE)
            if f.read(1):
                content += f"\n.... File {file_path} truncated at {READ_SIZE} characters"

        return content
    except Exception as e:
        return f"Error occurred while retreiving file contents: {e}"


if __name__ == "__main__":
    print(get_file_content("calculator", "lorem.txt"))
