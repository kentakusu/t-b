from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


@dataclass
class PageContent:
    url: str
    title: str
    text_content: str
    links: list[dict[str, str]] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    screenshot: bytes | None = None
    accessibility_tree: dict[str, Any] | None = None


class BrowserEngine:
    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._history: list[str] = []
        self._history_index: int = -1

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def navigate(self, url: str) -> PageContent:
        if not self._page:
            raise RuntimeError("Browser not started")

        if not url.startswith(("http://", "https://", "file://", "data:")):
            url = "https://" + url

        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            await self._page.wait_for_timeout(2000)

        self._history = self._history[: self._history_index + 1]
        self._history.append(url)
        self._history_index = len(self._history) - 1

        return await self._extract_content()

    async def go_back(self) -> PageContent | None:
        if self._history_index > 0:
            self._history_index -= 1
            url = self._history[self._history_index]
            if self._page:
                await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return await self._extract_content()
        return None

    async def go_forward(self) -> PageContent | None:
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            url = self._history[self._history_index]
            if self._page:
                await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return await self._extract_content()
        return None

    async def reload(self) -> PageContent:
        if self._page:
            await self._page.reload(wait_until="domcontentloaded", timeout=30000)
        return await self._extract_content()

    async def click_link(self, url: str) -> PageContent:
        return await self.navigate(url)

    async def execute_js(self, script: str) -> Any:
        if not self._page:
            raise RuntimeError("Browser not started")
        return await self._page.evaluate(script)

    async def scroll_down(self) -> None:
        if self._page:
            await self._page.evaluate("window.scrollBy(0, window.innerHeight)")

    async def scroll_up(self) -> None:
        if self._page:
            await self._page.evaluate("window.scrollBy(0, -window.innerHeight)")

    async def take_screenshot(self) -> bytes | None:
        if not self._page:
            return None
        return await self._page.screenshot(type="png", full_page=False)

    async def _extract_content(self, retries: int = 2) -> PageContent:
        if not self._page:
            raise RuntimeError("Browser not started")

        for attempt in range(retries + 1):
            try:
                return await self._do_extract_content()
            except Exception as e:
                if "Execution context was destroyed" in str(e) and attempt < retries:
                    await self._page.wait_for_load_state("domcontentloaded", timeout=10000)
                    continue
                raise

    async def _do_extract_content(self) -> PageContent:
        if not self._page:
            raise RuntimeError("Browser not started")

        title = await self._page.title()
        url = self._page.url

        text_content = await self._page.evaluate("""() => {
            function extractText(node, depth = 0) {
                const results = [];
                const BLOCK_TAGS = new Set([
                    'DIV', 'P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
                    'LI', 'TR', 'BLOCKQUOTE', 'PRE', 'SECTION', 'ARTICLE',
                    'HEADER', 'FOOTER', 'NAV', 'MAIN', 'ASIDE', 'FIGURE',
                    'FIGCAPTION', 'DETAILS', 'SUMMARY', 'TABLE', 'THEAD',
                    'TBODY', 'TFOOT', 'DT', 'DD', 'UL', 'OL', 'BR', 'HR'
                ]);
                const SKIP_TAGS = new Set([
                    'SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG', 'TEMPLATE'
                ]);

                for (const child of node.childNodes) {
                    if (child.nodeType === Node.TEXT_NODE) {
                        const text = child.textContent.trim();
                        if (text) results.push(text);
                    } else if (child.nodeType === Node.ELEMENT_NODE) {
                        const tag = child.tagName;
                        if (SKIP_TAGS.has(tag)) continue;

                        const style = window.getComputedStyle(child);
                        if (style.display === 'none' || style.visibility === 'hidden') continue;

                        const isBlock = BLOCK_TAGS.has(tag);
                        const prefix = tag === 'LI' ? '  • ' :
                                       tag.match(/^H[1-6]$/) ? '\\n' + '#'.repeat(parseInt(tag[1])) + ' ' :
                                       tag === 'BR' ? '\\n' :
                                       tag === 'HR' ? '\\n---\\n' :
                                       '';

                        if (isBlock && results.length > 0) results.push('\\n');
                        if (prefix) results.push(prefix);

                        const childText = extractText(child, depth + 1);
                        if (childText) results.push(childText);

                        if (isBlock) results.push('\\n');
                    }
                }
                return results.join('');
            }
            return extractText(document.body);
        }""")

        links = await self._page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .filter(a => {
                    const style = window.getComputedStyle(a);
                    return style.display !== 'none' && style.visibility !== 'hidden';
                })
                .slice(0, 200)
                .map((a, i) => ({
                    index: i,
                    text: (a.textContent || '').trim().substring(0, 100),
                    href: a.href,
                    title: a.title || ''
                }));
        }""")

        images = await self._page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img[src]'))
                .filter(img => {
                    const style = window.getComputedStyle(img);
                    return style.display !== 'none' && img.naturalWidth > 1;
                })
                .slice(0, 50)
                .map(img => ({
                    src: img.src,
                    alt: img.alt || '',
                    width: img.naturalWidth,
                    height: img.naturalHeight
                }));
        }""")

        screenshot = await self.take_screenshot()

        return PageContent(
            url=url,
            title=title,
            text_content=text_content,
            links=links,
            images=images,
            screenshot=screenshot,
        )

    @property
    def current_url(self) -> str:
        if self._page:
            return self._page.url
        return ""

    @property
    def can_go_back(self) -> bool:
        return self._history_index > 0

    @property
    def can_go_forward(self) -> bool:
        return self._history_index < len(self._history) - 1
