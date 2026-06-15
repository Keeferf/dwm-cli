"""Keyboard-navigable menus using readchar and rich Live rendering."""

from typing import List, Optional

from readchar import key, readkey
from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from dwm_cli.ui.console import console, get_global_header


def interactive_menu(
    options: List[str],
    title: str = "Menu",
    prompt_text: str = "↑/↓  move • Enter  select • Esc/q  cancel",
    header: Optional[RenderableType] = None,
) -> Optional[int]:
    """
    Show an interactive menu with arrow key navigation.
    Highlights the full width of the menu.
    """
    if not options:
        return None
    selected = 0

    # Use global header if no explicit header given
    if header is None:
        header = get_global_header()

    # Compute the maximum line length (bullet + space + option text)
    max_len = max(len(f"• {opt}") for opt in options)

    def render() -> RenderableType:
        lines = []
        for idx, opt in enumerate(options):
            line_text = f"• {opt}"
            # Pad to full width (add spaces to the right)
            padded = line_text.ljust(max_len)
            if idx == selected:
                line = Text(padded, style="reverse")
            else:
                line = Text(padded)
            lines.append(line)
        menu_panel = Panel(
            Group(*lines),
            title=title,
            subtitle=prompt_text,
            border_style="blue",
        )
        if header is not None:
            return Group(header, menu_panel)
        return menu_panel

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
