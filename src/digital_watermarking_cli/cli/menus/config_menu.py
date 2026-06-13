"""Configuration and profile management menu."""

from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from digital_watermarking_cli.config.settings import (
    list_profiles,
    switch_profile,
    create_profile,
    delete_profile,
    get_current_profile_name,
    DEFAULT_PROFILE_NAME
)
from digital_watermarking_cli.ui.console import console, create_numbered_table, create_profile_table


def manage_configurations() -> None:
    """Interactive menu for managing configuration profiles."""
    while True:
        current_profile = get_current_profile_name()
        menu_content = (
            f"[bold]Current profile:[/] [cyan]{current_profile}[/]\n\n"
            "1. List all profiles\n"
            "2. Switch to another profile\n"
            "3. Create new profile (copy from current or defaults)\n"
            "4. Delete a profile (cannot delete default)\n"
            "5. Back to main menu"
        )
        console.print(Panel(menu_content, title="Manage Configurations", border_style="blue"))
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="5")

        if choice == "1":
            _list_profiles_action(current_profile)
        elif choice == "2":
            _switch_profile_action()
        elif choice == "3":
            _create_profile_action(current_profile)
        elif choice == "4":
            _delete_profile_action()
        elif choice == "5":
            break


def _list_profiles_action(current_profile: str) -> None:
    """Display all available profiles."""
    profiles = list_profiles()
    table = create_profile_table(profiles, current_profile)
    console.print(table)
    Prompt.ask("\nPress Enter to continue", default="")


def _switch_profile_action() -> None:
    """Switch to a different profile."""
    profiles = list_profiles()
    table = create_numbered_table(profiles, title="Select Profile")
    console.print(table)
    
    sel = Prompt.ask("Select profile by number or name", default="")
    
    try:
        idx = int(sel) - 1
        if 0 <= idx < len(profiles):
            new_profile = profiles[idx]
        else:
            new_profile = sel
    except ValueError:
        new_profile = sel
    
    if switch_profile(new_profile):
        console.print(f"[green]Switched to profile '{new_profile}'[/]")
    else:
        console.print(f"[red]Profile '{new_profile}' does not exist.[/]")
    
    Prompt.ask("\nPress Enter to continue", default="")


def _create_profile_action(current_profile: str) -> None:
    """Create a new profile."""
    new_name = Prompt.ask("Name for new profile")
    
    if not new_name or not new_name.strip():
        console.print("[red]Invalid name.[/]")
        return
    
    use_current = Confirm.ask("Copy from current profile?", default=True)
    source = current_profile if use_current else None
    
    if create_profile(new_name, source):
        console.print(f"[green]Profile '{new_name}' created.[/]")
    else:
        console.print(f"[red]Profile '{new_name}' already exists.[/]")
    
    Prompt.ask("\nPress Enter to continue", default="")


def _delete_profile_action() -> None:
    """Delete a profile (except default)."""
    profiles = [p for p in list_profiles() if p != DEFAULT_PROFILE_NAME]
    
    if not profiles:
        console.print("[yellow]No deletable profiles (only default exists).[/]")
        return
    
    table = create_numbered_table(profiles, title="Deletable Profiles")
    console.print(table)
    
    sel = Prompt.ask("Select profile to delete by number or name", default="")
    
    try:
        idx = int(sel) - 1
        if 0 <= idx < len(profiles):
            to_delete = profiles[idx]
        else:
            to_delete = sel
    except ValueError:
        to_delete = sel
    
    if to_delete == DEFAULT_PROFILE_NAME:
        console.print("[red]Cannot delete default profile.[/]")
    elif delete_profile(to_delete):
        console.print(f"[green]Profile '{to_delete}' deleted.[/]")
    else:
        console.print(f"[red]Profile '{to_delete}' does not exist.[/]")
    
    Prompt.ask("\nPress Enter to continue", default="")