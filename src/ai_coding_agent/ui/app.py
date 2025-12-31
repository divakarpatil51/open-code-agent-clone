import logging
from textual import work
from textual.logging import TextualHandler
import json
from textual.reactive import reactive
import ollama
from ai_coding_agent.agent import Agent, Role
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
    LoadingIndicator,
    TextArea,
)


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


class ChatTextArea(TextArea):
    content = reactive(ollama.Message(role="none", content=""))

    def watch_content(self, updated_content: ollama.Message):
        if not updated_content.content:
            return

        if updated_content.role == Role.USER:
            self.insert(f"👤: {updated_content.content}", self.document.end)
        else:
            try:
                data = json.loads(updated_content.content or "")
                self.insert(
                    f"🤖: {json.dumps(data, indent=4)}",
                    self.document.end,
                )
            except json.JSONDecodeError:
                self.insert(f"🤖: {updated_content.content}", self.document.end)
        self.insert("\n\n", self.document.end)


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

        handler = TextualHandler()
        logging.getLogger("agent").addHandler(handler)
        logging.getLogger("agent").setLevel(logging.INFO)

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                yield ChatTextArea(id="chat-list", read_only=True)
                yield Vertical(
                    Input(placeholder="Enter your query..", id="query-input"),
                    Model(id="model"),
                    LoadingIndicator(name="Loading..."),
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

    def _update_loader_state(self, display: bool) -> None:
        self.query_one(LoadingIndicator).display = display

    def _update_content_from_resp(self, resp: ollama.ChatResponse) -> None:
        self.query_one("#model", Model).model = resp.model or self.agent.model

        chat_list = self.query_one("#chat-list", ChatTextArea)
        chat_list.content = resp.message

        self.query_one("#token", Token).token += (resp.prompt_eval_count or 0) + (
            resp.eval_count or 0
        )

        if resp.total_duration:
            duration_sec = resp.total_duration / 1e9
            self.query_one("#response-time", ResponseTime).duration = duration_sec

        if resp.done_reason:
            self.query_one("#done-reason", DoneReason).reason = resp.done_reason

        chat_list.scroll_end(animate=False)

    @work(thread=True)
    def load_data(self, query: str):
        chat_list = self.query_one("#chat-list", ChatTextArea)
        try:
            self.app.call_from_thread(self._update_loader_state, True)

            self.app.call_from_thread(
                chat_list.__setattr__,
                "content",
                ollama.Message(role=Role.USER, content=query),
            )

            resp: ollama.ChatResponse = self.agent.generate_response(query)

            self.app.call_from_thread(self._update_content_from_resp, resp)

        except Exception as e:
            self.app.call_from_thread(
                chat_list.__setattr__,
                "content",
                ollama.Message(role=Role.ASSISTANT, content=f"Error: {str(e)}"),
            )
        finally:
            self.app.call_from_thread(self._update_loader_state, False)


class ChatApp(App):
    TITLE = "AI Coding Agent"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ChatWindow(id="chat-window")
        yield Footer()


if __name__ == "__main__":
    ChatApp().run()
