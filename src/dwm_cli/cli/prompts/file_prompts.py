"""File selection and input collection prompts."""

from pathlib import Path
from typing import List, Optional
from rich.prompt import Prompt

from dwm_cli.utils.image_helpers import is_supported_image
from dwm_cli.dialogs.file_dialog import select_file_dialog
from dwm_cli.ui.console import console


def prompt_for_single_file(prompt_text: str, filetypes: list) -> Optional[Path]:
    """
    Prompt user to select a single file via browse or manual entry.
    
    Args:
        prompt_text: Display text for the prompt
        filetypes: List of file type tuples
    
    Returns:
        Path object or None
    """
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
        return path
    else:
        return Path(Prompt.ask("Input image path"))


def prompt_for_multiple_files(prompt_text: str, filetypes: list) -> List[Path]:
    """
    Prompt user to select multiple files via file browser.
    
    Args:
        prompt_text: Display text for the prompt
        filetypes: List of file type tuples
    
    Returns:
        List of Path objects
    """
    paths = select_file_dialog(f"Select images ({prompt_text})", filetypes, mode="open", multiple=True)
    
    if paths is None or len(paths) == 0:
        console.print("[yellow]No files selected. Falling back to single image entry.[/]")
        return [Path(Prompt.ask("Input image path"))]
    
    console.print(f"[green]Selected {len(paths)} files.[/]")
    return paths


def prompt_for_folder() -> Optional[Path]:
    """
    Prompt user to select a folder.
    
    Returns:
        Path object or None
    """
    folder = select_file_dialog("Select folder containing images", [], mode="folder")
    return folder


def get_images_from_folder_prompt(folder: Optional[Path]) -> List[Path]:
    """
    Get images from a folder with error handling.
    
    Args:
        folder: Path to folder or None
    
    Returns:
        List of image Paths, or fallback single image entry
    """
    if folder is None:
        console.print("[yellow]No folder selected. Falling back to single image entry.[/]")
        return [Path(Prompt.ask("Input image path"))]
    
    image_paths = [p for p in Path(folder).iterdir() if is_supported_image(p)]
    
    if not image_paths:
        console.print("[red]No supported image files found in that folder. Falling back to single image entry.[/]")
        return [Path(Prompt.ask("Input image path"))]
    
    console.print(f"[green]Found {len(image_paths)} supported images.[/]")
    return image_paths


def get_input_paths_interactive(prompt_text: str, filetypes: list) -> List[Path]:
    """
    Interactive menu for selecting image input (single, multiple, or folder).
    
    Args:
        prompt_text: Display text for the initial prompt
        filetypes: List of file type tuples
    
    Returns:
        List of Path objects
    """
    console.print(f"\n[bold cyan]{prompt_text}[/]")
    console.print("  1. Single image (manual path or browse)")
    console.print("  2. Multiple images (browse, multi-select)")
    console.print("  3. Folder (process all images inside)")
    choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")

    if choice == "1":
        path = prompt_for_single_file("an image", filetypes)
        return [path] if path else []
    
    elif choice == "2":
        return prompt_for_multiple_files(prompt_text, filetypes)
    
    elif choice == "3":
        folder = prompt_for_folder()
        return get_images_from_folder_prompt(folder)
    
    else:
        console.print("[red]Invalid choice. Using single image manual entry.[/]")
        return [Path(Prompt.ask("Input image path"))]