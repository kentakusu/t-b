from __future__ import annotations

import os
import shutil
from io import BytesIO

from PIL import Image
from rich.text import Text


HALF_BLOCK = "▄"
UPPER_HALF = "▀"


def detect_image_protocol() -> str:
    term = os.environ.get("TERM", "")
    term_program = os.environ.get("TERM_PROGRAM", "")

    if "kitty" in term_program.lower():
        return "kitty"
    if "iterm" in term_program.lower():
        return "iterm2"

    if shutil.which("img2sixel"):
        return "sixel"

    return "unicode"


def render_image_unicode(
    image_data: bytes,
    max_width: int = 80,
    max_height: int = 40,
) -> str:
    try:
        img = Image.open(BytesIO(image_data))
        img = img.convert("RGB")

        aspect = img.width / img.height
        width = min(max_width, img.width)
        height = int(width / aspect / 2)
        height = min(height, max_height)
        width = min(width, int(height * aspect * 2))

        if width < 1 or height < 1:
            return "[image too small]"

        img = img.resize((width, height * 2), Image.LANCZOS)

        lines = []
        for y in range(0, height * 2, 2):
            line = []
            for x in range(width):
                top_r, top_g, top_b = img.getpixel((x, y))
                if y + 1 < height * 2:
                    bot_r, bot_g, bot_b = img.getpixel((x, y + 1))
                else:
                    bot_r, bot_g, bot_b = top_r, top_g, top_b

                fg = f"\033[38;2;{bot_r};{bot_g};{bot_b}m"
                bg = f"\033[48;2;{top_r};{top_g};{top_b}m"
                line.append(f"{bg}{fg}{HALF_BLOCK}")

            lines.append("".join(line) + "\033[0m")

        return "\n".join(lines)
    except Exception as e:
        return f"[image error: {e}]"


def render_screenshot(
    screenshot_data: bytes,
    terminal_width: int = 120,
    terminal_height: int = 40,
) -> str:
    return render_image_unicode(
        screenshot_data,
        max_width=terminal_width,
        max_height=terminal_height,
    )


def image_to_text_placeholder(alt: str, src: str) -> Text:
    text = Text()
    display_alt = alt if alt else "image"
    text.append(f"[🖼 {display_alt}]", style="italic dim")
    return text
