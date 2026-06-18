"""File selection prompts – selection, validation, and retry orchestration."""

from enum import Enum
from pathlib import Path
from typing import List, Optional

from rich.prompt import Prompt

from dwm_cli.dialogs.file_dialog import select_file_dialog
from dwm_cli.ui.console import console
from dwm_cli.ui.menu_utils import interactive_menu
from dwm_cli.utils.image_helpers import validate_image

# Use "*" to show every file (works on all platforms)
ALL_FILES_FILETYPE = [("All files", "*")]


class RetryAction(Enum):
    """Actions to take when no valid image is selected."""

    BROWSE = "browse"
    MANUAL = "manual"
    CANCEL = "cancel"


# ---------- Pure selection functions (no validation) ----------


def prompt_for_single_file(prompt_text: str) -> Optional[Path]:
    """
    Ask the user to pick a single file (browse or manual entry).
    Returns the selected Path, or None if cancelled.
    No validation is performed – the caller must validate.
    """
    options = ["Browse from file explorer", "Enter path manually"]
    idx = interactive_menu(options, title=f"Select {prompt_text}")
    if idx is None:
        return None

    if idx == 0:  # Browse
        result = select_file_dialog(
            f"Select {prompt_text}",
            ALL_FILES_FILETYPE,
            mode="open",
            multiple=False,
        )
        if result is None:
            return None
        return result if isinstance(result, Path) else None

    else:  # idx == 1 (Manual entry)
        while True:
            raw = Prompt.ask("Input image path")
            if not raw.strip():
                console.print("[red]Path cannot be empty.[/]")
                continue
            return Path(raw)


def prompt_for_multiple_files(prompt_text: str) -> List[Path]:
    """
    Ask the user to pick multiple files using the file browser.
    Returns a list of Paths (possibly empty if cancelled).
    No validation is performed – the caller must validate.
    """
    result = select_file_dialog(
        f"Select images ({prompt_text})",
        ALL_FILES_FILETYPE,
        mode="open",
        multiple=True,
    )
    if result is None:
        return []
    if isinstance(result, Path):
        return [result]
    return result  # already a list


# ---------- Retry helper (shared) ----------


def _show_retry_menu() -> Optional[RetryAction]:
    """Show a menu when no valid images were selected."""
    options = ["Browse again", "Enter path manually", "Cancel"]
    idx = interactive_menu(options, title="No valid images selected")
    if idx is None or idx == 2:
        return RetryAction.CANCEL
    return RetryAction.BROWSE if idx == 0 else RetryAction.MANUAL


# ---------- Orchestrator with validation + retry + mode ----------


def get_input_paths_interactive(
    prompt_text: str, mode: Optional[str] = None
) -> List[Path]:
    """
    Interactive image selection with validation and retry.

    Args:
        prompt_text: Title for the selection menu.
        mode: If None, shows a submenu to choose single/multiple.
              If "single", directly prompts for one file.
              If "multiple", directly prompts for multiple files.

    Returns:
        List of valid image paths (may be empty if user cancels).
    """
    while True:
        # ----- Step 1: Determine mode if not forced -----
        if mode is None:
            mode_options = ["Single image", "Multiple images"]
            mode_idx = interactive_menu(mode_options, title=prompt_text)
            if mode_idx is None:
                return []
            current_mode = "single" if mode_idx == 0 else "multiple"
        else:
            current_mode = mode

        # ----- Step 2: Get raw paths (no validation) -----
        raw_paths: List[Path] = []
        if current_mode == "single":
            p = prompt_for_single_file("an image")
            if p:
                raw_paths = [p]
        else:  # "multiple"
            raw_paths = prompt_for_multiple_files(prompt_text)

        if not raw_paths:
            console.print("[yellow]No files selected.[/]")
            if mode is not None:
                # For forced mode, just return empty
                return []
            retry = Prompt.ask("Try again? ([y]/n)", choices=["y", "n"], default="y")
            if retry.lower() != "y":
                return []
            continue

        # ----- Step 3: Validate each path -----
        valid_paths = [p for p in raw_paths if validate_image(p)]
        invalid_paths = [p for p in raw_paths if p not in valid_paths]

        if invalid_paths:
            console.print("[yellow]Skipping invalid/unsupported images:[/]")
            for p in invalid_paths:
                console.print(f"  • {p.name}")

        if valid_paths:
            console.print(f"[green]✓ Selected {len(valid_paths)} valid image(s).[/]")
            return valid_paths

        # ----- Step 4: No valid images – ask what to do -----
        console.print("[red]No valid images were selected.[/]")
        action = _show_retry_menu()

        if action == RetryAction.CANCEL:
            return []
        elif action == RetryAction.BROWSE:
            continue  # loop again, same mode
        else:  # MANUAL – fallback to manual entry for a single file
            console.print("[yellow]Manual entry only supports a single file.[/]")
            single = prompt_for_single_file("an image (manual)")
            if single and validate_image(single):
                console.print(f"[green]✓ Valid image: {single}[/]")
                return [single]
            else:
                if single:
                    console.print(f"[red]✗ Invalid image: {single}[/]")
                continue  # try again
