import os
from enum import StrEnum, auto
from time import time_ns
from functions import get_file_content, write_file, get_files_info
from textual import log

import ollama


system_prompt = """
You are a helpful AI coding agent.

You can interact with the codebase only via the provided function calling mechanism. You can recursively check the directory contents as well.

AVAILABLE TOOLS:
- get_files_info(directory)
- get_file_content(file_path)
- write_file(file_path, content)

REMEMBER:
- Use tools only if necessary
- Code has already defined working directory for all the tools. You just have to pass the remaining required parameters.

"""

MAX_ITERATIONS = 20


class Role(StrEnum):
    ASSISTANT = auto()
    SYSTEM = auto()
    TOOL = auto()
    USER = auto()


def call_function(function_call, verbose=False) -> str:
    if verbose:
        log(f"Calling function: {function_call.name} ({function_call.arguments})")
    else:
        log(f"Calling function: {function_call.name} ")

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


class EnvironmentVariableNotSet(Exception): ...


class Agent:
    def __init__(self):
        self._model = os.getenv("MODEL", "")
        if not self._model:
            raise EnvironmentVariableNotSet("Please set MODEL env variable")

        self.client = ollama.Client()
        self.messages: list[ollama.Message] = [
            ollama.Message(role=Role.SYSTEM, content=system_prompt)
        ]

    def generate_response(self, query: str) -> ollama.ChatResponse:
        self.messages.append(ollama.Message(role=Role.USER, content=query))
        query_start_time = time_ns()
        return self._generate_response(
            loop_count=1, query_start_time=query_start_time, accumulated_response=None
        )

    def get_active_context(self) -> list[ollama.Message]:
        if len(self.messages) <= 20:
            return self.messages

        return [self.messages[0]] + self.messages[-19:]

    def _generate_response(
        self,
        loop_count: int = 1,
        query_start_time: int = 0,
        accumulated_response: ollama.ChatResponse | None = None,
    ) -> ollama.ChatResponse:
        if loop_count > MAX_ITERATIONS:
            error_msg = ollama.Message(
                role=Role.ASSISTANT,
                content="Error: Maximum iteration limit reached. Task too complex or stuck in loop.",
            )
            self.messages.append(error_msg)

            if accumulated_response:
                return ollama.ChatResponse(
                    model=accumulated_response.model or self.model,
                    message=error_msg,
                    done=True,
                    done_reason="length",
                    total_duration=time_ns() - query_start_time,
                    load_duration=accumulated_response.load_duration,
                    prompt_eval_count=accumulated_response.prompt_eval_count,
                    prompt_eval_duration=accumulated_response.prompt_eval_duration,
                    eval_count=accumulated_response.eval_count,
                    eval_duration=accumulated_response.eval_duration,
                )
            else:
                return ollama.ChatResponse(
                    model=self.model,
                    message=error_msg,
                    done=True,
                    done_reason="length",
                    total_duration=time_ns() - query_start_time,
                )

        response: ollama.ChatResponse = self.client.chat(
            model=self.model,
            messages=self.get_active_context(),
            tools=[get_file_content, get_files_info, write_file],
        )

        # Accumulate metrics from this iteration
        if accumulated_response:
            accumulated_response = ollama.ChatResponse(
                model=response.model or accumulated_response.model,
                message=response.message,
                done=response.done,
                done_reason=response.done_reason,
                total_duration=response.total_duration,
                load_duration=(accumulated_response.load_duration or 0)
                + (response.load_duration or 0),
                prompt_eval_count=(accumulated_response.prompt_eval_count or 0)
                + (response.prompt_eval_count or 0),
                prompt_eval_duration=(accumulated_response.prompt_eval_duration or 0)
                + (response.prompt_eval_duration or 0),
                eval_count=(accumulated_response.eval_count or 0)
                + (response.eval_count or 0),
                eval_duration=(accumulated_response.eval_duration or 0)
                + (response.eval_duration or 0),
            )
        else:
            accumulated_response = response

        self.messages.append(response.message)

        if not response.message.tool_calls:
            log(self.messages)
            return accumulated_response

        for tool in response.message.tool_calls or []:
            resp: str = call_function(tool.function, False)
            if resp.startswith("Error"):
                message = ollama.Message(
                    role=Role.ASSISTANT,
                    content=f"Some error: {resp}",
                )
                self.messages.append(message)
                accumulated_response.message = message
                return accumulated_response

            self.messages.append(
                ollama.Message(
                    role=Role.TOOL,
                    tool_name=tool.function.name,
                    content=resp,
                )
            )

        return self._generate_response(
            loop_count=loop_count + 1,
            query_start_time=query_start_time,
            accumulated_response=accumulated_response,
        )

    @property
    def model(self) -> str:
        return self._model

    def get_all_messages(self) -> list[ollama.Message]:
        return self.messages
