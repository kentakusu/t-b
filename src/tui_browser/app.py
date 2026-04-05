from __future__ import annotations

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Footer,
    Header,
    Input,
    Static,
    RichLog,
)
from rich.text import Text

import re

from .engine import BrowserEngine, PageContent
from .renderer import PageRenderer
from .image_handler import render_screenshot


DEFAULT_URL = "https://example.com"


class URLBar(Input):
    pass


class StatusBar(Static):
    def update_status(self, text: str) -> None:
        self.update(text)


class ContentView(RichLog):
    pass


class BrowserApp(App):
    TITLE = "TUI Browser"
    CSS = """
    Screen {
        layout: vertical;
    }

    #url-bar-container {
        height: 3;
        dock: top;
        background: $surface;
        padding: 0 1;
    }

    #url-bar-container Horizontal {
        height: 3;
        width: 100%;
    }

    #nav-buttons {
        width: 14;
        height: 3;
        content-align: center middle;
    }

    #url-input {
        width: 1fr;
    }

    #content {
        height: 1fr;
        scrollbar-size: 1 1;
        border: solid $primary;
        padding: 0 1;
    }

    #status-bar {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }

    #view-mode {
        width: 12;
        height: 3;
        content-align: center middle;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "focus_url", "URL Bar"),
        Binding("ctrl+r", "reload", "Reload"),
        Binding("ctrl+left", "go_back", "Back"),
        Binding("ctrl+right", "go_forward", "Forward"),
        Binding("ctrl+s", "screenshot_mode", "Screenshot"),
        Binding("ctrl+g", "open_link", "Go to Link #"),
        Binding("ctrl+f", "show_forms", "Forms"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f5", "reload", "Reload", show=False),
    ]

    def __init__(self, start_url: str | None = None) -> None:
        super().__init__()
        self._engine = BrowserEngine()
        self._renderer = PageRenderer()
        self._current_content: PageContent | None = None
        self._start_url = start_url or DEFAULT_URL
        self._screenshot_mode = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="url-bar-container"):
            with Horizontal():
                yield Static(" ◀ ▶ ↻ ", id="nav-buttons")
                yield URLBar(
                    placeholder="Enter URL...",
                    value=self._start_url,
                    id="url-input",
                )
                yield Static(" [TXT] ", id="view-mode")
        yield ContentView(id="content", wrap=True, highlight=True, markup=True)
        yield StatusBar("Ready", id="status-bar")
        yield Footer()

    async def on_mount(self) -> None:
        self._status("Starting browser engine...")
        self._start_engine()

    @work(exclusive=True)
    async def _start_engine(self) -> None:
        try:
            await self._engine.start()
            self._status("Browser engine ready. Loading page...")
            await self._do_navigate(self._start_url)
        except Exception as e:
            self._status(f"Engine start failed: {e}")
            self._content_view.write(
                Text(f"Failed to start browser engine:\n{e}", style="bold red")
            )

    @on(Input.Submitted, "#url-input")
    async def on_url_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return

        if cmd.isdigit():
            link = self._renderer.get_link_by_index(int(cmd))
            if link:
                self._url_input.value = link.href
                self._navigate(link.href)
                return

        form_match = re.match(r'^([fbs])(\d+)\s*(.*)', cmd, re.DOTALL)
        if form_match:
            action, idx_str, value = form_match.groups()
            idx = int(idx_str)
            self._handle_form_action(action, idx, value.strip())
            return

        self._navigate(cmd)

    @work(exclusive=True, group="navigation")
    async def _navigate(self, url: str) -> None:
        await self._do_navigate(url)

    async def _do_navigate(self, url: str) -> None:
        self._status(f"Loading: {url}")
        content_view = self._content_view
        content_view.clear()
        content_view.write(Text("Loading...", style="italic dim"))

        try:
            content = await self._engine.navigate(url)
            self._current_content = content

            self._url_input.value = content.url
            self.title = content.title or "TUI Browser"

            content_view.clear()

            if self._screenshot_mode and content.screenshot:
                self._render_screenshot(content)
            else:
                self._render_text(content)

            link_count = len(content.links)
            img_count = len(content.images)
            form_count = len(content.forms)
            self._status(
                f"✓ {content.title} | {link_count} links, {form_count} forms | "
                f"# = link, f/b/s<N> = form, Ctrl+F = list forms"
            )
        except Exception as e:
            content_view.clear()
            content_view.write(
                Text(f"Navigation error:\n{e}", style="bold red")
            )
            self._status(f"Error: {e}")

    def _render_text(self, content: PageContent) -> None:
        content_view = self._content_view
        terminal_width = self.size.width - 4

        title_text = Text()
        title_text.append(f"\n {content.title}\n", style="bold magenta underline")
        title_text.append(f" {content.url}\n", style="dim")
        title_text.append("─" * min(terminal_width, 80) + "\n", style="dim")
        content_view.write(title_text)

        rendered, links = self._renderer.render_page(
            content.text_content,
            content.links,
            terminal_width=terminal_width,
        )
        content_view.write(rendered)

        if links:
            content_view.write(Text("\n"))
            content_view.write(Text("─" * min(terminal_width, 80), style="dim"))
            content_view.write(self._renderer.get_link_list_text())

    def _render_screenshot(self, content: PageContent) -> None:
        if not content.screenshot:
            self._content_view.write(Text("No screenshot available", style="italic"))
            return

        content_view = self._content_view
        terminal_width = self.size.width - 4
        terminal_height = self.size.height - 8

        screenshot_text = render_screenshot(
            content.screenshot,
            terminal_width=terminal_width,
            terminal_height=terminal_height,
        )
        content_view.write(Text.from_ansi(screenshot_text))

    def action_focus_url(self) -> None:
        self._url_input.focus()
        self._url_input.action_select_all()

    def action_reload(self) -> None:
        self._do_reload()

    @work(exclusive=True, group="navigation")
    async def _do_reload(self) -> None:
        self._status("Reloading...")
        try:
            content = await self._engine.reload()
            self._current_content = content
            self._content_view.clear()
            if self._screenshot_mode and content.screenshot:
                self._render_screenshot(content)
            else:
                self._render_text(content)
            self._status(f"✓ Reloaded: {content.title}")
        except Exception as e:
            self._status(f"Reload error: {e}")

    def action_go_back(self) -> None:
        self._do_go_back()

    @work(exclusive=True, group="navigation")
    async def _do_go_back(self) -> None:
        if not self._engine.can_go_back:
            self._status("No previous page")
            return
        self._status("Going back...")
        content = await self._engine.go_back()
        if content:
            self._current_content = content
            self._url_input.value = content.url
            self._content_view.clear()
            if self._screenshot_mode and content.screenshot:
                self._render_screenshot(content)
            else:
                self._render_text(content)
            self._status(f"✓ {content.title}")

    def action_go_forward(self) -> None:
        self._do_go_forward()

    @work(exclusive=True, group="navigation")
    async def _do_go_forward(self) -> None:
        if not self._engine.can_go_forward:
            self._status("No next page")
            return
        self._status("Going forward...")
        content = await self._engine.go_forward()
        if content:
            self._current_content = content
            self._url_input.value = content.url
            self._content_view.clear()
            if self._screenshot_mode and content.screenshot:
                self._render_screenshot(content)
            else:
                self._render_text(content)
            self._status(f"✓ {content.title}")

    def action_screenshot_mode(self) -> None:
        self._screenshot_mode = not self._screenshot_mode
        mode_label = "IMG" if self._screenshot_mode else "TXT"
        view_mode = self.query_one("#view-mode", Static)
        view_mode.update(f" [{mode_label}] ")

        if self._current_content:
            self._content_view.clear()
            if self._screenshot_mode and self._current_content.screenshot:
                self._render_screenshot(self._current_content)
            else:
                self._render_text(self._current_content)

        self._status(
            f"View mode: {'Screenshot (image)' if self._screenshot_mode else 'Text'}"
        )

    def action_open_link(self) -> None:
        self._url_input.value = ""
        self._url_input.placeholder = "Enter link number..."
        self._url_input.focus()

    def action_show_forms(self) -> None:
        if not self._current_content:
            self._status("No page loaded")
            return
        content_view = self._content_view
        content_view.clear()
        form_text = PageRenderer.get_form_list_text(self._current_content.forms)
        content_view.write(form_text)
        self._status(
            f"Forms: {len(self._current_content.forms)} elements | "
            f"f<N> <text> = type, b<N> = click, s<N> = submit"
        )
        self._url_input.value = ""
        self._url_input.placeholder = "f0 hello / b0 / s0..."
        self._url_input.focus()

    @work(exclusive=True, group="navigation")
    async def _handle_form_action(self, action: str, index: int, value: str) -> None:
        try:
            if action == "f":
                await self._engine.interact_form(index, value or None)
                self._status(f"Typed into element {index}")
                self._url_input.value = ""
                self._url_input.placeholder = f"s{index} to submit, or continue..."
            elif action == "b":
                content = await self._engine.interact_form(index)
                if content:
                    self._current_content = content
                    self._url_input.value = content.url
                    self._content_view.clear()
                    self._render_text(content)
                    self._status(f"Clicked element {index}")
                else:
                    self._status(f"Clicked element {index}")
            elif action == "s":
                selector = f"[data-tui-form-idx='{index}']"
                content = await self._engine.submit_form(selector)
                self._current_content = content
                self._url_input.value = content.url
                self._content_view.clear()
                self._render_text(content)
                self._status(f"Submitted form via element {index}")
        except Exception as e:
            self._status(f"Form action error: {e}")

    async def on_unmount(self) -> None:
        await self._engine.stop()

    @property
    def _content_view(self) -> ContentView:
        return self.query_one("#content", ContentView)

    @property
    def _url_input(self) -> URLBar:
        return self.query_one("#url-input", URLBar)

    def _status(self, text: str) -> None:
        try:
            status = self.query_one("#status-bar", StatusBar)
            status.update_status(text)
        except Exception:
            pass


def run(url: str | None = None) -> None:
    app = BrowserApp(start_url=url)
    app.run()
