"""Keyboard-navigable menus using readchar and rich Live rendering."""

from typing import List, Optional

from readchar import key, readkey
from rich import box
from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from dwm_cli.ui.console import console, get_global_header

BRAND = "rgb(125,122,188)"


def _numbered_menu(options: List[str], title: str) -> Optional[int]:
    """Non-interactive fallback for when stdin is not a TTY."""
    lines = [Text(f"{i:>2}.  {opt}") for i, opt in enumerate(options, 1)]
    console.print(
        Panel(
            Group(*lines),
            title=f"[bold cyan]{title}[/]",
            border_style=BRAND,
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    try:
        answer = Prompt.ask(
            "Select number",
            choices=[str(i) for i in range(1, len(options) + 1)],
            default="1",
        )
    except (EOFError, KeyboardInterrupt):
        return None
    return int(answer) - 1


def interactive_menu(
    options: List[str],
    title: str = "Menu",
    prompt_text: str = "↑/↓ navigate · Enter select · Esc/q cancel",
    header: Optional[RenderableType] = None,
) -> Optional[int]:
    """
    Show an interactive menu with arrow key navigation.
    Highlights the full width of the menu.
    Falls back to a numbered menu when stdin is not a TTY.
    """
    if not options:
        return None

    # Use global header if no explicit header given
    if header is None:
        header = get_global_header()

    if not console.is_terminal:
        return _numbered_menu(options, title)

    selected = 0

    # Compute the maximum row width so the highlight bar stays uniform
    max_len = max(len(f"▶ {idx + 1:>2}  {opt}") for idx, opt in enumerate(options))

    def render() -> RenderableType:
        lines = []
        for idx, opt in enumerate(options):
            marker = "▶" if idx == selected else " "
            padded = f"{marker} {idx + 1:>2}  {opt}".ljust(max_len)
            if idx == selected:
                lines.append(Text(padded, style=f"bold white on {BRAND}"))
            else:
                lines.append(Text(padded, style="rgb(198,196,224)"))
        menu_panel = Panel(
            Group(*lines),
            title=f"[bold cyan]{title}[/]",
            subtitle=Text(prompt_text, style="dim"),
            subtitle_align="center",
            border_style=BRAND,
            box=box.ROUNDED,
            padding=(1, 2),
        )
        if header is not None:
            return Group(header, menu_panel)
        return menu_panel

    try:
        with Live(render(), console=console, auto_refresh=False, screen=True) as live:
            while True:
                live.update(render(), refresh=True)
                k = readkey()
                if k == key.UP and selected > 0:
                    selected -= 1
                elif k == key.DOWN and selected < len(options) - 1:
                    selected += 1
                elif k == key.ENTER or k == "\r":
                    return selected
                elif k == key.ESC or k == "q":
                    return None
    except (EOFError, KeyboardInterrupt):
        return None