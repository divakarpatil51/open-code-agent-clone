import attrs


@attrs.define
class ToolResponse:
    has_error: bool
    content: str
    error_message: str | None = None

    @classmethod
    def success(cls, content: str) -> "ToolResponse":
        return cls(has_error=False, content=content)

    @classmethod
    def error(cls, error_message: str) -> "ToolResponse":
        return cls(has_error=True, content="", error_message=error_message)
