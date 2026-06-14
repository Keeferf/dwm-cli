from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box

from dwm_cli.config.settings import (
    list_profiles,
    switch_profile,
    create_profile,
    delete_profile,
    get_current_profile_name,
    DEFAULT_PROFILE_NAME,
    load_config,
)
from dwm_cli.ui.console import console, wait_for_enter
from dwm_cli.ui.menu_utils import interactive_menu


def manage_configurations() -> None:
    """Interactive menu for managing configuration profiles using keyboard navigation."""

    def action_list_profiles():
        """Show all profiles with their full configuration settings."""
        current = get_current_profile_name()
        profiles = list_profiles()

        if not profiles:
            console.print("[yellow]No profiles found.[/]")
            wait_for_enter()
            return

        for profile in profiles:
            try:
                settings = load_config(profile)
            except Exception as e:
                console.print(f"[red]Error loading settings for '{profile}': {e}[/]")
                continue

            setting_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
            setting_table.add_column("Setting", style="cyan", no_wrap=True)
            setting_table.add_column("Value", style="white")

            for key, value in settings.items():
                value_str = str(value)
                if len(value_str) > 60 and key == "font":
                    value_str = "..." + value_str[-50:]
                setting_table.add_row(key, value_str)

            title_style = "bold green" if profile == current else "bold"
            border_style = "green" if profile == current else "blue"
            panel = Panel(
                setting_table,
                title=f"[{title_style}]{profile}[/]",
                border_style=border_style,
                padding=(0, 1)
            )
            console.print(panel)
            console.print()

        wait_for_enter()

    def action_switch_profile():
        """Switch the active configuration profile."""
        profiles = list_profiles()
        from dwm_cli.ui.console import create_numbered_table
        table = create_numbered_table(profiles, title="Select Profile")
        console.print(table)

        sel = Prompt.ask("Select profile by number or name", default="")
        # Map both number strings and names to the actual profile
        profile_map = {str(i+1): p for i, p in enumerate(profiles)}
        profile_map.update({p: p for p in profiles})
        new_profile = profile_map.get(sel)

        if new_profile is None:
            console.print("[red]Invalid selection.[/]")
        elif switch_profile(new_profile):
            console.print(f"[green]✓ Switched to profile '{new_profile}'[/]")
        else:
            console.print(f"[red]✗ Profile '{new_profile}' does not exist.[/]")
        wait_for_enter()

    def action_create_profile():
        """Create a new configuration profile, optionally copying from the current profile."""
        current = get_current_profile_name()
        new_name = Prompt.ask("[cyan]Name for new profile[/]")
        if not new_name or not new_name.strip():
            console.print("[red]Invalid name.[/]")
            wait_for_enter()
            return

        use_current = Confirm.ask("Copy from current profile?", default=True)
        source = current if use_current else None

        if create_profile(new_name, source):
            console.print(f"[green]✓ Profile '{new_name}' created.[/]")
        else:
            console.print(f"[red]✗ Profile '{new_name}' already exists.[/]")
        wait_for_enter()

    def action_delete_profile():
        """Delete a configuration profile (default profile cannot be deleted)."""
        profiles = [p for p in list_profiles() if p != DEFAULT_PROFILE_NAME]
        if not profiles:
            console.print("[yellow]No deletable profiles (only default exists).[/]")
            wait_for_enter()
            return

        from dwm_cli.ui.console import create_numbered_table
        table = create_numbered_table(profiles, title="Deletable Profiles")
        console.print(table)

        sel = Prompt.ask("Select profile to delete by number or name", default="")
        profile_map = {str(i+1): p for i, p in enumerate(profiles)}
        profile_map.update({p: p for p in profiles})
        to_delete = profile_map.get(sel)

        if to_delete is None:
            console.print("[red]Invalid selection.[/]")
        elif to_delete == DEFAULT_PROFILE_NAME:
            console.print("[red]Cannot delete default profile.[/]")
        elif delete_profile(to_delete):
            console.print(f"[green]✓ Profile '{to_delete}' deleted.[/]")
        else:
            console.print(f"[red]✗ Profile '{to_delete}' does not exist.[/]")
        wait_for_enter()

    def _back():
        """Sentinel action to exit the configuration menu."""
        raise StopIteration

    menu_actions = {
        "List all profiles": action_list_profiles,
        "Switch to another profile": action_switch_profile,
        "Create new profile (copy from current or defaults)": action_create_profile,
        "Delete a profile (cannot delete default)": action_delete_profile,
        "Back to main menu": _back,
    }
    options = list(menu_actions.keys())

    while True:
        current_profile = get_current_profile_name()
        title = f"Manage Configurations – Current: {current_profile}"

        try:
            idx = interactive_menu(options, title=title)
            if idx is None:          # User pressed Esc/q
                break
            menu_actions[options[idx]]()
        except StopIteration:
            break