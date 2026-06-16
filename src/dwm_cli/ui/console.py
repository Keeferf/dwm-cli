"""Rich console setup and helper utilities."""

from pathlib import Path
from typing import Any, Dict, Optional

from rich import box
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table

# Import the default config keys to ensure consistent column ordering
from dwm_cli.config.settings import DEFAULT_CONFIG

# Global console instance
console = Console()

# Global header that will be shown on every menu screen
_global_header: Optional[RenderableType] = None


def set_global_header(header: RenderableType) -> None:
    """Store the header (banner + credits) to be reused across menus."""
    global _global_header
    _global_header = header


def get_global_header() -> Optional[RenderableType]:
    """Return the stored global header, if any."""
    return _global_header


def clear_screen() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def display_panel(content: str, title: str = "", border_style: str = "blue") -> None:
    """Display a Rich panel with content."""
    panel = Panel(
        content,
        title=f"[bold green]{title}[/]" if title else None,
        border_style=border_style,
        padding=(0, 1),
    )
    console.print(panel)


def create_simple_table(
    rows: list,
    headers: tuple = ("Setting", "Value"),
    header_styles: tuple = ("dim cyan", "bold white"),
) -> Table:
    """
    Create a simple two-column table.

    Args:
        rows: List of tuples [(key, value), ...]
        headers: Column header names
        header_styles: Style for each column

    Returns:
        Rich Table object
    """
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column(headers[0], style=header_styles[0], no_wrap=True)
    table.add_column(headers[1], style=header_styles[1])

    for key, value in rows:
        table.add_row(key, value)

    return table


def create_numbered_table(items: list, title: str = "", style: str = "cyan") -> Table:
    """
    Create a numbered table for selection menus.

    Args:
        items: List of items to display
        title: Table title
        style: Style for item column

    Returns:
        Rich Table object
    """
    table = Table(title=title, box=box.SIMPLE)
    table.add_column("#", style="dim")
    table.add_column("Item", style=style)

    for i, item in enumerate(items, 1):
        table.add_row(str(i), str(item))

    return table


def create_profile_table(profiles: list, current_profile: str) -> Table:
    """Create a table showing available profiles with current marker."""
    table = Table(title="Available Profiles", box=box.ROUNDED)
    table.add_column("Profile Name", style="cyan")
    table.add_column("Current", style="green")

    for p in profiles:
        current_marker = "✓" if p == current_profile else ""
        table.add_row(p, current_marker)

    return table


def display_info_table(config: Dict[str, Any], output_dir: Path, profile: str) -> None:
    """
    Display current profile settings in a horizontal table,
    matching the style of the configuration menu's profile list.
    """
    table = Table(
        title=f"Active Profile: {profile}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    # First column: profile name
    table.add_column("Profile Name", style="bold", no_wrap=True)
    # One column per setting (order preserved from DEFAULT_CONFIG)
    for key in DEFAULT_CONFIG.keys():
        table.add_column(key, overflow="fold")

    # Build the single row for the current profile
    row = [profile]
    for key in DEFAULT_CONFIG.keys():
        value = config.get(key, "N/A")
        if key == "output_dir":
            value = str(
                output_dir
            )  # use the passed output_dir (may differ from config)
        elif key == "font" and isinstance(value, str) and len(value) > 60:
            value = "..." + value[-50:]  # truncate long font paths
        elif key in ("opacity", "scale") and isinstance(value, (int, float)):
            value = f"{float(value):.2f}"
        else:
            value = str(value)
        row.append(value)

    table.add_row(*row)
    console.print(table)
    console.print()  # blank line for readability


def wait_for_enter(message: str = "Press Enter to continue") -> None:
    """
    Display a styled panel and wait for the user to press Enter.
    """
    panel = Panel(f"[dim]{message}[/]", border_style="blue", padding=(0, 1))
    console.print(panel)
    input()
