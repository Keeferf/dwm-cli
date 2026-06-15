"""File selection and input collection prompts."""

from pathlib import Path
from typing import List, Optional

from rich.prompt import Prompt

from dwm_cli.dialogs.file_dialog import select_file_dialog
from dwm_cli.ui.console import console
from dwm_cli.ui.menu_utils import interactive_menu
from dwm_cli.utils.image_helpers import validate_image

# Use "*" to show every file (works on all platforms)
ALL_FILES_FILETYPE = [("All files", "*")]


def _is_valid_image_file(path: Path) -> bool:
    """Check if a file exists and is a valid image (Pillow can open it)."""
    return path.exists() and validate_image(path)


def _handle_invalid_selection() -> Optional[str]:
    """
    Show a menu when an invalid file is selected.
    Returns:
        "browse" -> try file browser again
        "manual" -> go to manual entry
        None -> cancel (return to caller, which may propagate cancellation)
    """
    options = ["Browse again", "Enter path manually", "Cancel"]
    idx = interactive_menu(options, title="Invalid file selected")
    if idx is None or idx == 2:  # Esc/q or Cancel
        return None
    return "browse" if idx == 0 else "manual"


def prompt_for_single_file(
    prompt_text: str, filetypes: Optional[list] = None
) -> Optional[Path]:
    """
    Prompt user to select a single file via browse or manual entry.
    The file browser shows *all* file types. After selection the file is
    validated as an image; if invalid, the user is shown a menu to retry.
    """
    while True:
        options = ["Browse from file explorer", "Enter path manually"]
        idx = interactive_menu(options, title="Select input method")
        if idx is None:
            return None

        if idx == 0:  # Browse
            while True:
                result = select_file_dialog(
                    f"Select {prompt_text}",
                    ALL_FILES_FILETYPE,
                    mode="open",
                    multiple=False,
                )
                if result is None:
                    console.print("[yellow]No file selected.[/]")
                    break

                selected_path = (
                    result
                    if isinstance(result, Path)
                    else (result[0] if result else None)
                )
                if selected_path and _is_valid_image_file(selected_path):
                    console.print(f"[green]✓ Valid image: {selected_path}[/]")
                    return selected_path
                else:
                    console.print(
                        f"[red]✗ Invalid or unsupported image: {selected_path}[/]"
                    )
                    action = _handle_invalid_selection()
                    if action is None:
                        break
                    elif action == "browse":
                        continue
                    else:  # manual
                        idx = 1
                        break
        else:  # idx == 1 (Manual entry)
            while True:
                raw = Prompt.ask("Input image path")
                if not raw.strip():
                    console.print("[red]Path cannot be empty.[/]")
                    continue
                selected_path = Path(raw)
                if _is_valid_image_file(selected_path):
                    console.print(f"[green]✓ Valid image: {selected_path}[/]")
                    return selected_path
                else:
                    console.print(
                        f"[red]✗ Invalid or unsupported image: {selected_path}[/]"
                    )
                    action = _handle_invalid_selection()
                    if action is None:
                        return None
                    elif action == "browse":
                        idx = 0
                        break
                    else:  # manual again, loop continues
                        continue


def prompt_for_multiple_files(
    prompt_text: str, filetypes: Optional[list] = None
) -> List[Path]:
    """
    Prompt user to select multiple files via file browser (shows all files).
    Invalid image files are filtered out. If no valid files are selected,
    the user is shown a menu to retry.
    """
    while True:
        result = select_file_dialog(
            f"Select images ({prompt_text})",
            ALL_FILES_FILETYPE,
            mode="open",
            multiple=True,
        )

        if result is None:
            paths = []
        elif isinstance(result, Path):
            paths = [result]
        else:
            paths = result

        valid_paths = []
        invalid_paths = []
        for p in paths:
            if _is_valid_image_file(p):
                valid_paths.append(p)
            else:
                invalid_paths.append(p)

        if invalid_paths:
            console.print(
                "[yellow]The following files are not valid images and will be skipped:[/]"
            )
            for bad in invalid_paths:
                console.print(f"  • {bad.name}")

        if valid_paths:
            console.print(f"[green]✓ Selected {len(valid_paths)} valid image(s).[/]")
            return valid_paths
        else:
            console.print("[red]No valid image files selected.[/]")
            action = _handle_invalid_selection()
            if action is None:
                return []
            elif action == "browse":
                continue
            else:  # manual entry fallback for multiple
                console.print(
                    "[yellow]Multiple manual entry not supported. Falling back to single image.[/]"
                )
                single = prompt_for_single_file("an image")
                return [single] if single else []


def prompt_for_folder() -> Optional[Path]:
    """Prompt user to select a folder (no filtering)."""
    result = select_file_dialog("Select folder containing images", [], mode="folder")
    if result is None:
        return None
    if isinstance(result, list):
        return result[0] if result else None
    return result


def get_images_from_folder_prompt(folder: Optional[Path]) -> List[Path]:
    """
    Get images from a folder. Only files that can be opened by Pillow are kept.
    """
    if folder is None:
        console.print(
            "[yellow]No folder selected. Falling back to single image entry.[/]"
        )
        single = prompt_for_single_file("an image")
        return [single] if single else []

    image_paths = []
    invalid = []

    for p in Path(folder).iterdir():
        if p.is_file():
            if validate_image(p):
                image_paths.append(p)
            else:
                invalid.append(p)

    if invalid:
        console.print("[yellow]Skipping files that are not valid images:[/]")
        for f in invalid:
            console.print(f"  • {f.name}")

    if not image_paths:
        console.print("[red]No valid image files found in that folder.[/]")
        single = prompt_for_single_file("an image")
        return [single] if single else []

    console.print(f"[green]✓ Found {len(image_paths)} valid image(s).[/]")
    return image_paths


def get_input_paths_interactive(
    prompt_text: str, filetypes: Optional[list] = None
) -> List[Path]:
    """
    Interactive menu for selecting image input (single, multiple, or folder).
    Uses keyboard navigation (↑/↓, Enter, Esc/q) with global header.
    The `filetypes` argument is ignored – all dialogs show *all* files.
    """
    options = [
        "Single image (manual path or browse)",
        "Multiple images (browse, multi‑select)",
        "Folder (process all images inside)",
    ]
    choice_idx = interactive_menu(options, title=prompt_text)

    if choice_idx is None:
        return []

    if choice_idx == 0:
        path = prompt_for_single_file("an image")
        return [path] if path else []
    elif choice_idx == 1:
        return prompt_for_multiple_files(prompt_text)
    else:
        folder = prompt_for_folder()
        return get_images_from_folder_prompt(folder)
