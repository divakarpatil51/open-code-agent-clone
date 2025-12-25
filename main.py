from enum import StrEnum, auto
import pprint
from functions import get_file_content, write_file, get_files_info

import ollama


system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- List file contents
- Write or overwrite to a file

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.

Stop calling tools once you have enough information to answer.
Do not re-call tools to verify unless explicitly required.
"""

MODEL = "llama3.2:3b"

class Role(StrEnum):
    ASSISTANT = auto()
    SYSTEM = auto()
    TOOL = auto()
    USER = auto()

def call_function(function_call, verbose=False) -> str:
    if verbose:
        print(f"Calling function: {function_call.name} ({function_call.arguments})")
    else:
        print(f"Calling function: {function_call.name} ")

    function_map = {
        "get_file_content": get_file_content,
        "get_files_info": get_files_info,
        "write_file": write_file,
    }

    fn = function_map.get(function_call.name)
    if not fn:
        return f"Error: Invalid function: {function_call.name}"

    args = dict(function_call.arguments) if function_call.arguments else {}
    args["wd"] = "./calculator"
    return fn(**args)


def generate_response(
    client: ollama.Client, messages: list[ollama.Message], loop_count=1
) -> list[ollama.Message]:
    if loop_count > 20:
        messages.append(
            ollama.Message(
                role=Role.ASSISTANT,
                content="Error: Maximum iteration limit reached. Task too complex or stuck in loop.",
            )
        )
        return messages

    stream: ollama.ChatResponse = client.chat(
        model=MODEL,
        messages=messages,
        tools=[get_file_content, get_files_info, write_file],
    )

    if not stream.message.tool_calls:
        messages.append(stream.message)
        return messages

    for tool in stream.message.tool_calls:
        resp: str = call_function(tool.function, False)
        messages.append(ollama.Message(role=Role.TOOL, content=resp))
        if resp.startswith("Error"):
            messages.append(
                ollama.Message(
                    role=Role.ASSISTANT,
                    content=resp,
                )
            )
            return messages
    return generate_response(client, messages, loop_count + 1)


def main():
    client = ollama.Client()

    messages: list[ollama.Message] = [
        ollama.Message(role=Role.SYSTEM, content=system_prompt)
    ]
    while True:
        prompt = input("User (enter /q to exit): ")
        if prompt == "/q":
            break
        messages.append(ollama.Message(role=Role.USER, content=prompt))
        generate_response(client, messages)
        pprint.pprint(list(filter(lambda message: message.role == Role.ASSISTANT, messages)))



if __name__ == "__main__":
    main()
