"""Configuration and profile management menu."""

from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from dwm_cli.config.settings import (
    list_profiles,
    switch_profile,
    create_profile,
    delete_profile,
    get_current_profile_name,
    DEFAULT_PROFILE_NAME
)
from dwm_cli.ui.console import console, create_numbered_table, create_profile_table


def manage_configurations() -> None:
    """Interactive menu for managing configuration profiles using dictionary mapping."""

    # ----- Internal action functions (no return value needed) -----
    def action_list_profiles():
        current = get_current_profile_name()
        profiles = list_profiles()
        table = create_profile_table(profiles, current)
        console.print(table)
        Prompt.ask("\nPress Enter to continue", default="")

    def action_switch_profile():
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

    def action_create_profile():
        current = get_current_profile_name()
        new_name = Prompt.ask("Name for new profile")
        if not new_name or not new_name.strip():
            console.print("[red]Invalid name.[/]")
            Prompt.ask("\nPress Enter to continue", default="")
            return
        use_current = Confirm.ask("Copy from current profile?", default=True)
        source = current if use_current else None
        if create_profile(new_name, source):
            console.print(f"[green]Profile '{new_name}' created.[/]")
        else:
            console.print(f"[red]Profile '{new_name}' already exists.[/]")
        Prompt.ask("\nPress Enter to continue", default="")

    def action_delete_profile():
        profiles = [p for p in list_profiles() if p != DEFAULT_PROFILE_NAME]
        if not profiles:
            console.print("[yellow]No deletable profiles (only default exists).[/]")
            Prompt.ask("\nPress Enter to continue", default="")
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

    def action_back():
        # No action needed – just signals to exit the config menu loop
        pass

    # Map option keys to their action functions
    menu_actions = {
        "1": action_list_profiles,
        "2": action_switch_profile,
        "3": action_create_profile,
        "4": action_delete_profile,
        "5": action_back,
    }

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
        choice = Prompt.ask("Select option", choices=list(menu_actions.keys()), default="5")

        action = menu_actions.get(choice)
        if action:
            action()
            if choice == "5":   # Back option – break out of the config menu loop
                break
        else:
            console.print("[red]Invalid choice, try again.[/]")