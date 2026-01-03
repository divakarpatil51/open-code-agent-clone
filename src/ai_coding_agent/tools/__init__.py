from ._get_file_content import get_file_content
from ._get_files_info import get_files_info
from ._write_file import write_file
from ._dataclasses import ToolResponse


available_functions = {
    "get_file_content": get_file_content,
    "get_files_info": get_files_info,
    "write_file": write_file,
}

ollama_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_file_content",
            "description": "This tool retrieves file contents for the given file path",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file for which to get file contents",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_files_info",
            "description": "This tool provides file size and directory status in the specified directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The path of directory to list files from.",
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "This tool write contents to file present at given working directory and file path..",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path to which content needs to be written",
                    },
                    "content": {
                        "type": "string",
                        "description": "Data to be written",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    },
]
