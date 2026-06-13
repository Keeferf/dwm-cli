"""Rich console setup and helper utilities."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from pathlib import Path
from typing import Dict, Any


# Global console instance
console = Console()


def clear_screen() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def display_panel(content: str, title: str = "", border_style: str = "blue") -> None:
    """Display a Rich panel with content."""
    panel = Panel(
        content,
        title=f"[bold green]{title}[/]" if title else None,
        border_style=border_style,
        padding=(0, 1)
    )
    console.print(panel)


def create_simple_table(
    rows: list,
    headers: tuple = ("Setting", "Value"),
    header_styles: tuple = ("dim cyan", "bold white")
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


def create_numbered_table(
    items: list,
    title: str = "",
    style: str = "cyan"
) -> Table:
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
    """Display current profile and settings in a formatted table."""
    def get_val(key, default="—"):
        return config.get(key, default)
    
    rows = [
        ("Profile", f"[cyan]{profile}[/]"),
        ("Position", get_val("position", "bottom-right")),
        ("Opacity", f"{get_val('opacity', 0.5):.2f}"),
        ("Font size", str(get_val("font_size", 36))),
        ("Text color", get_val("text_color", "white")),
        ("Image scale", f"{get_val('scale', 1.0):.2f}"),
        ("Output dir", f"[dim]{output_dir}[/]"),
    ]
    
    table = create_simple_table(rows)
    panel = Panel(
        table,
        title="[bold green]Active Profile[/]",
        border_style="blue",
        padding=(0, 1)
    )
    console.print(panel)
    console.print()