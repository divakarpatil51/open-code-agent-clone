from textual import work
import json
from rich.segment import Segment
import rich.console
from textual.reactive import reactive
import ollama
from agent import Agent
from textual.widget import Widget
from textual.containers import (
    Horizontal,
    Vertical,
)
from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    Rule,
    RichLog,
    LoadingIndicator,
)


class ChatMessage:
    def __init__(self, message: ollama.Message):
        self.message: ollama.Message = message

    def __rich_console__(self, console, console_options) -> rich.console.RenderResult:
        if self.message.role.lower() == "user":
            yield Segment(f"👤: {self.message.content}")
        else:
            try:
                data = json.loads(self.message.content or "")
                yield f"🤖: {data.values()}"
            except json.JSONDecodeError:
                yield f"🤖: {self.message.content}"
        yield "\n"


class Token(Label):
    token = reactive(0)

    def watch_token(self, updated_value: int):
        self.update(f"🎫 {updated_value} tokens consumed")


class Model(Label):
    model = reactive("")

    def watch_model(self, updated_value: str):
        self.update(f"[yellow]Model: {updated_value}")


class ResponseTime(Label):
    duration = reactive(0.0)

    def watch_duration(self, updated_value: float):
        if updated_value > 0:
            self.update(f"⏱️  Response: {updated_value:.2f}s")
        else:
            self.update("")


class DoneReason(Label):
    reason = reactive("")

    def watch_reason(self, updated_value: str):
        if not updated_value:
            self.update("")
            return
        emoji = "✓" if updated_value == "stop" else "⚠️"
        self.update(f"{emoji} Status: {updated_value}")


class ChatWindow(Widget):
    DEFAULT_CSS = """
    LoadingIndicator {
        layer: above;
        background: $background 80%;
    }
    #left-panel {
        width: 75vw;
    }
    #right-panel {
        width: 25vw;
    }
    #repo {
        width: 100%;
        height: auto;  
        text-wrap: wrap;
        background: $panel;
        padding: 1;
        border-top: solid $primary;
    }

    #chat-list {
        height: 90%;
        padding: 1;
    }

    #left-panel-bottom-container {
        border-top: solid $primary;
        height: 10%;
    }

    """

    def on_mount(self):
        self.agent = Agent()
        self.query_one("#model", Model).model = self.agent.model
        self.query_one(LoadingIndicator).display = False
        self.query_one("#query-input", Input).focus()

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                yield RichLog(id="chat-list", auto_scroll=True, markup=True)
                yield Vertical(
                    Input("Enter your query..", id="query-input"),
                    Model(id="model"),
                    Horizontal(LoadingIndicator(name="Loading...")),
                    id="left-panel-bottom-container",
                )

            yield Rule(orientation="vertical", line_style="thick")

            with Vertical(
                id="right-panel",
            ):
                with Vertical(
                    id="context-content",
                ):
                    yield Label("Context:")
                    yield Token(id="token")
                    yield ResponseTime(id="response-time")
                    yield DoneReason(id="done-reason")

    def on_input_submitted(self, event: Input.Submitted):
        query = event.value.strip()
        if not query:
            return

        query_input = self.query_one("#query-input", Input)
        query_input.clear()

        self.load_data(query)

        query_input.focus()

    @work(thread=True)
    def load_data(self, query: str):
        chat_list = self.query_one("#chat-list", RichLog)
        try:
            self.query_one(LoadingIndicator).display = True

            chat_list.write(ChatMessage(ollama.Message(role="User", content=query)))

            resp = self.agent.generate_response(query)
            self.query_one("#model", Model).model = resp.model or self.agent.model

            chat_list.write(ChatMessage(resp.message))

            self.query_one("#token", Token).token += (resp.prompt_eval_count or 0) + (
                resp.eval_count or 0
            )

            if resp.total_duration:
                duration_sec = resp.total_duration / 1e9
                self.query_one("#response-time", ResponseTime).duration = duration_sec

            if resp.done_reason:
                self.query_one("#done-reason", DoneReason).reason = resp.done_reason

            chat_list.scroll_end(animate=False)

        except Exception as e:
            chat_list.write(
                ChatMessage(
                    ollama.Message(role="Assistant", content=f"Error: {str(e)}")
                )
            )
        finally:
            self.query_one(LoadingIndicator).display = False


class ChatApp(App):
    TITLE = "Open Code Clone"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ChatWindow(id="chat-window")
        yield Footer()


if __name__ == "__main__":
    ChatApp().run()
