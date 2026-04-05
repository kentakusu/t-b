from __future__ import annotations

import re
from dataclasses import dataclass

from rich.console import Console, ConsoleOptions, RenderResult
from rich.markup import escape
from rich.text import Text
from rich.panel import Panel


@dataclass
class LinkInfo:
    index: int
    text: str
    href: str
    title: str


class PageRenderer:
    def __init__(self) -> None:
        self._links: list[LinkInfo] = []

    def render_page(
        self,
        text_content: str,
        links: list[dict[str, str]],
        terminal_width: int = 120,
    ) -> tuple[Text, list[LinkInfo]]:
        self._links = [
            LinkInfo(
                index=link.get("index", i),
                text=link.get("text", ""),
                href=link.get("href", ""),
                title=link.get("title", ""),
            )
            for i, link in enumerate(links)
        ]

        link_texts = {link.text.lower(): link for link in self._links if link.text}

        rendered = Text()
        lines = text_content.split("\n")

        for line in lines:
            stripped = line.rstrip()

            if stripped.startswith("######"):
                heading = stripped[6:].strip()
                rendered.append(f"      {heading}\n", style="bold")
            elif stripped.startswith("#####"):
                heading = stripped[5:].strip()
                rendered.append(f"     {heading}\n", style="bold")
            elif stripped.startswith("####"):
                heading = stripped[4:].strip()
                rendered.append(f"    {heading}\n", style="bold")
            elif stripped.startswith("###"):
                heading = stripped[3:].strip()
                rendered.append(f"   {heading}\n", style="bold cyan")
            elif stripped.startswith("##"):
                heading = stripped[2:].strip()
                rendered.append(f"  {heading}\n", style="bold blue")
            elif stripped.startswith("#"):
                heading = stripped[1:].strip()
                rendered.append(f" {heading}\n", style="bold magenta underline")
            elif stripped == "---":
                rendered.append("─" * min(terminal_width - 4, 80) + "\n", style="dim")
            elif stripped.startswith("  • "):
                item_text = stripped[4:]
                rendered.append("  • ", style="yellow")
                self._append_with_links(rendered, item_text, link_texts)
                rendered.append("\n")
            else:
                self._append_with_links(rendered, stripped, link_texts)
                rendered.append("\n")

        return rendered, self._links

    def _append_with_links(
        self,
        rendered: Text,
        text: str,
        link_texts: dict[str, LinkInfo],
    ) -> None:
        if not text:
            return

        text_lower = text.lower()
        matched = False
        for link_key, link_info in link_texts.items():
            if link_key and link_key in text_lower:
                parts = re.split(re.escape(link_info.text), text, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    if parts[0]:
                        rendered.append(parts[0])
                    rendered.append(
                        f"[{link_info.index}]{link_info.text}",
                        style="underline blue",
                    )
                    if parts[1]:
                        rendered.append(parts[1])
                    matched = True
                    break

        if not matched:
            rendered.append(text)

    def get_link_by_index(self, index: int) -> LinkInfo | None:
        for link in self._links:
            if link.index == index:
                return link
        return None

    def get_link_list_text(self) -> Text:
        text = Text()
        text.append("Links on this page:\n\n", style="bold underline")
        for link in self._links[:50]:
            display = link.text or link.href
            text.append(f"  [{link.index}] ", style="yellow bold")
            text.append(f"{display[:60]}", style="underline blue")
            text.append(f"  → {link.href[:80]}\n", style="dim")
        if len(self._links) > 50:
            text.append(f"\n  ... and {len(self._links) - 50} more links\n", style="dim")
        return text
