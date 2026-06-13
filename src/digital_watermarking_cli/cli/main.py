import typer
from pathlib import Path
from typing import Optional, List, Tuple, Union
import importlib.resources as resources

from digital_watermarking_cli.core.visible_watermark import add_text_watermark, add_image_watermark
from digital_watermarking_cli.utils.image_helpers import is_supported_image, validate_image
from digital_watermarking_cli.config.settings import (
    load_config, save_config, list_profiles, create_profile, delete_profile, switch_profile,
    get_current_profile_name, DEFAULT_PROFILE_NAME
)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich import box

# Initialize Rich console
console = Console()

app = typer.Typer(help="Watermarking CLI Tool", no_args_is_help=False)


def get_current_config():
    """Load the current active profile config."""
    return load_config()


def get_default_font_path() -> str:
    """Return absolute path to the bundled Roboto-Regular.ttf, or empty string if missing."""
    try:
        with resources.path("digital_watermarking_cli.core", "Roboto-Regular.ttf") as font_path:
            if font_path.exists():
                return str(font_path)
            return ""
    except (ImportError, FileNotFoundError, TypeError):
        return ""


def get_output_dir():
    """
    Return output directory from current config.
    If config has no output_dir or it's empty, default to Downloads folder.
    """
    config = get_current_config()
    out = config.get("output_dir", "")
    if out:
        path = Path(out).expanduser().resolve()
    else:
        path = Path.home() / "Downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def clear_screen():
    """Clear terminal for cleaner menus"""
    print("\033[2J\033[H", end="")


def select_file_dialog(title: str, filetypes: list, mode: str = "open", multiple: bool = False) -> Optional[Union[Path, List[Path]]]:
    """
    Open a native file dialog.
    - mode: 'open' (file), 'save' (file), 'folder'
    - multiple: for 'open' mode only, return list of Paths if True.
    Returns Path(s) or None if cancelled or tkinter unavailable.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        if mode == "folder":
            folder = filedialog.askdirectory(title=title)
            root.destroy()
            return Path(folder) if folder else None
        elif mode == "open":
            if multiple:
                files = filedialog.askopenfilenames(title=title, filetypes=filetypes)
                root.destroy()
                return [Path(f) for f in files] if files else None
            else:
                file = filedialog.askopenfilename(title=title, filetypes=filetypes)
                root.destroy()
                return Path(file) if file else None
        elif mode == "save":
            file = filedialog.asksaveasfilename(title=title, filetypes=filetypes)
            root.destroy()
            return Path(file) if file else None
        else:
            raise ValueError("mode must be 'open', 'save', or 'folder'")
    except (ImportError, tk.TclError):
        return None


def get_input_paths_interactive(prompt_text: str, filetypes: list) -> List[Path]:
    """Let user select single image, multiple images, or a folder for batch processing."""
    console.print(f"\n[bold cyan]{prompt_text}[/]")
    console.print("  1. Single image (manual path or browse)")
    console.print("  2. Multiple images (browse, multi-select)")
    console.print("  3. Folder (process all images inside)")
    choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")

    if choice == "1":
        console.print("  1. Browse from file explorer")
        console.print("  2. Enter path manually")
        sub = Prompt.ask("Choose", choices=["1", "2"], default="1")
        if sub == "1":
            path = select_file_dialog(f"Select {prompt_text}", filetypes, mode="open", multiple=False)
            if path is None:
                console.print("[yellow]No file selected. Falling back to manual entry.[/]")
                path = Path(Prompt.ask("Input image path"))
            else:
                console.print(f"[green]Selected: {path}[/]")
            return [path]
        else:
            return [Path(Prompt.ask("Input image path"))]

    elif choice == "2":
        paths = select_file_dialog(f"Select images ({prompt_text})", filetypes, mode="open", multiple=True)
        if paths is None or len(paths) == 0:
            console.print("[yellow]No files selected. Falling back to single image entry.[/]")
            return [Path(Prompt.ask("Input image path"))]
        console.print(f"[green]Selected {len(paths)} files.[/]")
        return paths

    elif choice == "3":
        folder = select_file_dialog(f"Select folder containing images", [], mode="folder")
        if folder is None:
            console.print("[yellow]No folder selected. Falling back to single image entry.[/]")
            return [Path(Prompt.ask("Input image path"))]
        image_paths = [p for p in Path(folder).iterdir() if is_supported_image(p)]
        if not image_paths:
            console.print("[red]No supported image files found in that folder. Falling back to single image entry.[/]")
            return [Path(Prompt.ask("Input image path"))]
        console.print(f"[green]Found {len(image_paths)} supported images.[/]")
        return image_paths

    else:
        console.print("[red]Invalid choice. Using single image manual entry.[/]")
        return [Path(Prompt.ask("Input image path"))]


def get_text_color() -> Tuple[int, int, int]:
    """
    Prompt user to choose a text color, using config as default.
    Returns RGB tuple.
    """
    config = get_current_config()
    default_hex = config.get("text_color", "#FFFFFF")
    console.print(f"\nSelect text color (default: [white]{default_hex}[/]):")
    console.print("  1. Black")
    console.print("  2. White")
    console.print("  3. Hex code (e.g., #FF5733)")
    choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")

    if choice == "1":
        return (0, 0, 0)
    elif choice == "2":
        return (255, 255, 255)
    elif choice == "3":
        while True:
            hex_code = Prompt.ask(f"Enter hex color", default=default_hex)
            hex_code = hex_code.lstrip('#').upper()
            if len(hex_code) == 6 and all(c in '0123456789ABCDEF' for c in hex_code):
                r = int(hex_code[0:2], 16)
                g = int(hex_code[2:4], 16)
                b = int(hex_code[4:6], 16)
                return (r, g, b)
            else:
                console.print("[red]Invalid hex code. Use format like FF5733 or #FF5733.[/]")
    else:
        console.print("[yellow]Invalid choice, using default white.[/]")
        return (255, 255, 255)


def prompt_text_watermark_batch(input_paths: List[Path]):
    """Apply text watermark to a list of images, saving to configured output_dir."""
    # Pre-validate images, skip invalid/corrupt ones
    valid_paths = []
    for p in input_paths:
        if validate_image(p):
            valid_paths.append(p)
        else:
            console.print(f"[red]Skipping invalid/corrupt image: {p.name}[/]")

    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        return

    config = get_current_config()
    output_dir = get_output_dir()
    text = Prompt.ask("Watermark text")
    pos_default = config.get("position", "bottom-right")
    position = Prompt.ask("Position (preset: bottom-right, top-left, center, etc. or X,Y)", default=pos_default)
    default_font = get_default_font_path()
    font_path_input = Prompt.ask(
        "Font path (leave empty to use Roboto font)",
        default=config.get("font", "")
    )
    if font_path_input == "":
        if default_font:
            font_path = default_font
        else:
            font_path = None
            console.print("[yellow]Bundled Roboto font not found, falling back to PIL default.[/]")
    else:
        font_path = font_path_input

    font_size = IntPrompt.ask("Font size", default=config.get("font_size", 36))
    opacity = FloatPrompt.ask("Opacity (0-1)", default=config.get("opacity", 0.5))
    text_color = get_text_color()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Applying text watermark...", total=len(valid_paths))
        for idx, input_path in enumerate(valid_paths, 1):
            output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"
            try:
                add_text_watermark(
                    input_path=input_path,
                    output_path=output_path,
                    text=text,
                    position=position,
                    font_path=font_path,
                    font_size=int(font_size),
                    opacity=float(opacity),
                    text_color=text_color,
                )
                progress.update(task, advance=1, description=f"[green]✓ {input_path.name}")
            except Exception as e:
                console.print(f"[red]Error on {input_path.name}: {e}[/]")
                progress.update(task, advance=1, description=f"[red]✗ {input_path.name} failed")
    console.print("[bold green]Batch text watermarking completed![/]")


def prompt_image_watermark_batch(input_paths: List[Path]):
    """Apply image watermark to a list of images, saving to configured output_dir."""
    valid_paths = []
    for p in input_paths:
        if validate_image(p):
            valid_paths.append(p)
        else:
            console.print(f"[red]Skipping invalid/corrupt image: {p.name}[/]")

    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        return

    config = get_current_config()
    output_dir = get_output_dir()
    watermark_path = get_input_paths_interactive("Watermark image (logo)", [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif")])[0]

    if not validate_image(watermark_path):
        console.print(f"[red]Watermark image is invalid or corrupted: {watermark_path}[/]")
        return

    pos_default = config.get("position", "bottom-right")
    position = Prompt.ask("Position (preset: bottom-right, top-left, center, etc. or X,Y)", default=pos_default)
    scale = FloatPrompt.ask("Scale factor (1.0 = original)", default=config.get("scale", 1.0))
    opacity = FloatPrompt.ask("Opacity (0-1)", default=config.get("opacity", 0.5))

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Applying image watermark...", total=len(valid_paths))
        for idx, input_path in enumerate(valid_paths, 1):
            output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"
            try:
                add_image_watermark(
                    input_path=input_path,
                    output_path=output_path,
                    watermark_path=watermark_path,
                    position=position,
                    scale=float(scale),
                    opacity=float(opacity),
                )
                progress.update(task, advance=1, description=f"[green]✓ {input_path.name}")
            except Exception as e:
                console.print(f"[red]Error on {input_path.name}: {e}[/]")
                progress.update(task, advance=1, description=f"[red]✗ {input_path.name} failed")
    console.print("[bold green]Batch image watermarking completed![/]")


def prompt_text_watermark():
    """Single-image text watermark"""
    console.print(Panel("[bold]Text Watermark (Single Image)[/]", style="cyan"))
    input_path = get_input_paths_interactive("Source image to watermark", [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")])[0]
    output_dir = get_output_dir()
    output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"
    config = get_current_config()
    text = Prompt.ask("Watermark text")
    pos_default = config.get("position", "bottom-right")
    position = Prompt.ask("Position (preset: bottom-right, top-left, center, etc. or X,Y)", default=pos_default)
    default_font = get_default_font_path()
    font_path_input = Prompt.ask(
        "Font path (leave empty to use Roboto font)",
        default=config.get("font", "")
    )
    if font_path_input == "":
        if default_font:
            font_path = default_font
        else:
            font_path = None
            console.print("[yellow]Bundled Roboto font not found, falling back to PIL default.[/]")
    else:
        font_path = font_path_input

    font_size = IntPrompt.ask("Font size", default=config.get("font_size", 36))
    opacity = FloatPrompt.ask("Opacity (0-1)", default=config.get("opacity", 0.5))
    text_color = get_text_color()

    try:
        add_text_watermark(
            input_path=input_path,
            output_path=output_path,
            text=text,
            position=position,
            font_path=font_path,
            font_size=int(font_size),
            opacity=float(opacity),
            text_color=text_color,
        )
        console.print(f"[bold green]✓ Text watermark added:[/] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")


def prompt_image_watermark():
    """Single-image image watermark"""
    console.print(Panel("[bold]Image Watermark (Single Image)[/]", style="cyan"))
    input_path = get_input_paths_interactive("Source image to watermark", [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")])[0]
    output_dir = get_output_dir()
    output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"
    config = get_current_config()
    watermark_path = get_input_paths_interactive("Watermark image (logo)", [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif")])[0]
    pos_default = config.get("position", "bottom-right")
    position = Prompt.ask("Position (preset: bottom-right, top-left, center, etc. or X,Y)", default=pos_default)
    scale = FloatPrompt.ask("Scale factor (1.0 = original)", default=config.get("scale", 1.0))
    opacity = FloatPrompt.ask("Opacity (0-1)", default=config.get("opacity", 0.5))

    try:
        add_image_watermark(
            input_path=input_path,
            output_path=output_path,
            watermark_path=watermark_path,
            position=position,
            scale=float(scale),
            opacity=float(opacity),
        )
        console.print(f"[bold green]✓ Image watermark added:[/] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")


def manage_configurations():
    """Submenu for managing config profiles."""
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
            profiles = list_profiles()
            table = Table(title="Available Profiles", box=box.ROUNDED)
            table.add_column("Profile Name", style="cyan")
            table.add_column("Current", style="green")
            for p in profiles:
                current_marker = "✓" if p == current_profile else ""
                table.add_row(p, current_marker)
            console.print(table)
            Prompt.ask("\nPress Enter to continue", default="")

        elif choice == "2":
            profiles = list_profiles()
            table = Table(title="Select Profile", box=box.SIMPLE)
            table.add_column("#", style="dim")
            table.add_column("Profile Name", style="cyan")
            for i, p in enumerate(profiles, 1):
                table.add_row(str(i), p)
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

        elif choice == "3":
            new_name = Prompt.ask("Name for new profile")
            if not new_name or not new_name.strip():
                console.print("[red]Invalid name.[/]")
                continue
            use_current = Confirm.ask("Copy from current profile?", default=True)
            source = current_profile if use_current else None
            if create_profile(new_name, source):
                console.print(f"[green]Profile '{new_name}' created.[/]")
            else:
                console.print(f"[red]Profile '{new_name}' already exists.[/]")
            Prompt.ask("\nPress Enter to continue", default="")

        elif choice == "4":
            profiles = [p for p in list_profiles() if p != DEFAULT_PROFILE_NAME]
            if not profiles:
                console.print("[yellow]No deletable profiles (only default exists).[/]")
            else:
                table = Table(title="Deletable Profiles", box=box.SIMPLE)
                table.add_column("#", style="dim")
                table.add_column("Profile Name", style="cyan")
                for i, p in enumerate(profiles, 1):
                    table.add_row(str(i), p)
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

        elif choice == "5":
            break


@app.callback(invoke_without_command=True)
def main_menu(ctx: typer.Context):
    """Interactive menu for watermarking tool. Run without arguments."""
    if ctx.invoked_subcommand is not None:
        return

    clear_screen()
    console.print(Panel("[bold cyan]Welcome to Watermark CLI Tool[/]", style="green", expand=False))

    while True:
        menu_options = (
            "1. Text watermark (single image)\n"
            "2. Image watermark (single image)\n"
            "3. Batch text watermark (multiple images/folder)\n"
            "4. Batch image watermark (multiple images/folder)\n"
            "5. Manage configurations (profiles)\n"
            "6. Exit"
        )
        console.print(Panel(menu_options, title="Main Menu", border_style="blue"))
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="6")

        if choice == "1":
            prompt_text_watermark()
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        elif choice == "2":
            prompt_image_watermark()
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        elif choice == "3":
            inputs = get_input_paths_interactive(
                "Select images for batch text watermark",
                [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
            )
            prompt_text_watermark_batch(inputs)
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        elif choice == "4":
            inputs = get_input_paths_interactive(
                "Select images for batch image watermark",
                [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
            )
            prompt_image_watermark_batch(inputs)
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        elif choice == "5":
            manage_configurations()
            clear_screen()
        elif choice == "6":
            console.print("[bold green]Goodbye! 👋[/]")
            raise typer.Exit()
        else:
            console.print("[red]Invalid choice, try again.[/]")


if __name__ == "__main__":
    app()