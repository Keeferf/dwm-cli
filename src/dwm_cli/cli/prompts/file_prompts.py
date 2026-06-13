"""File selection and input collection prompts."""

from pathlib import Path
from typing import List, Optional
from rich.prompt import Prompt
from rich.panel import Panel

from dwm_cli.utils.image_helpers import is_supported_image
from dwm_cli.dialogs.file_dialog import select_file_dialog
from dwm_cli.ui.console import console
from dwm_cli.ui.menu_utils import interactive_menu


def prompt_for_single_file(prompt_text: str, filetypes: list) -> Optional[Path]:
    """
    Prompt user to select a single file via browse or manual entry.
    Uses keyboard‑navigable menu with global header.
    """
    options = ["Browse from file explorer", "Enter path manually"]
    idx = interactive_menu(options, title="Select input method")
    # If user cancels (Esc/q), default to manual entry
    if idx is None:
        idx = 1  # "Enter path manually"

    if idx == 0:  # Browse
        path = select_file_dialog(f"Select {prompt_text}", filetypes, mode="open", multiple=False)
        if path is None:
            console.print("[yellow]No file selected. Falling back to manual entry.[/]")
            path = Path(Prompt.ask("Input image path"))
        else:
            console.print(f"[green]✓ Selected: {path}[/]")
        return path
    else:  # Manual entry
        return Path(Prompt.ask("Input image path"))


def prompt_for_multiple_files(prompt_text: str, filetypes: list) -> List[Path]:
    """
    Prompt user to select multiple files via file browser.
    """
    paths = select_file_dialog(f"Select images ({prompt_text})", filetypes, mode="open", multiple=True)
    
    if paths is None or len(paths) == 0:
        console.print("[yellow]No files selected. Falling back to single image entry.[/]")
        return [Path(Prompt.ask("Input image path"))]
    
    console.print(f"[green]✓ Selected {len(paths)} files.[/]")
    return paths


def prompt_for_folder() -> Optional[Path]:
    """
    Prompt user to select a folder.
    """
    folder = select_file_dialog("Select folder containing images", [], mode="folder")
    return folder


def get_images_from_folder_prompt(folder: Optional[Path]) -> List[Path]:
    """
    Get images from a folder with error handling.
    """
    if folder is None:
        console.print("[yellow]No folder selected. Falling back to single image entry.[/]")
        return [Path(Prompt.ask("Input image path"))]
    
    image_paths = [p for p in Path(folder).iterdir() if is_supported_image(p)]
    
    if not image_paths:
        console.print("[red]No supported image files found in that folder. Falling back to single image entry.[/]")
        return [Path(Prompt.ask("Input image path"))]
    
    console.print(f"[green]✓ Found {len(image_paths)} supported images.[/]")
    return image_paths


def get_input_paths_interactive(prompt_text: str, filetypes: list) -> List[Path]:
    """
    Interactive menu for selecting image input (single, multiple, or folder).
    Uses keyboard navigation (↑/↓, Enter, Esc/q) with global header.
    """
    options = [
        "Single image (manual path or browse)",
        "Multiple images (browse, multi‑select)",
        "Folder (process all images inside)"
    ]
    choice_idx = interactive_menu(options, title=prompt_text)
    
    # If user cancels (Esc/q), fallback to single image manual entry
    if choice_idx is None:
        choice_idx = 0

    if choice_idx == 0:  # Single image
        path = prompt_for_single_file("an image", filetypes)
        return [path] if path else []
    
    elif choice_idx == 1:  # Multiple images
        return prompt_for_multiple_files(prompt_text, filetypes)
    
    else:  # Folder
        folder = prompt_for_folder()
        return get_images_from_folder_prompt(folder)