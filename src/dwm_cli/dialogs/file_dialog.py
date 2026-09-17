"""File selection dialog abstraction using tkinter."""

from pathlib import Path
from typing import List, Optional, Union


def select_file_dialog(
    title: str, filetypes: list, mode: str = "open", multiple: bool = False
) -> Optional[Union[Path, List[Path]]]:
    """
    Open a file/folder selection dialog using tkinter.

    Args:
        title: Dialog window title
        filetypes: List of tuples like [("Image files", "*.jpg *.png")]
        mode: "open", "save", or "folder"
        multiple: If True, allow multi-select (only for mode="open")

    Returns:
        Path object, list of Path objects, or None if cancelled/unavailable.
    """
    try:
        import tkinter as tk
    except ImportError:
        # tkinter unavailable in this environment - prompt layer handles fallback
        return None

    from tkinter import filedialog

    try:
        root = tk.Tk()
    except tk.TclError:
        # No display available (headless) - fall back to manual entry upstream
        return None

    root.withdraw()
    root.attributes("-topmost", True)

    try:
        if mode == "folder":
            folder = filedialog.askdirectory(title=title)
            return Path(folder) if folder else None

        if mode == "open":
            if multiple:
                files = filedialog.askopenfilenames(title=title, filetypes=filetypes)
                return [Path(f) for f in files] if files else None
            file = filedialog.askopenfilename(title=title, filetypes=filetypes)
            return Path(file) if file else None

        if mode == "save":
            file = filedialog.asksaveasfilename(title=title, filetypes=filetypes)
            return Path(file) if file else None

        raise ValueError("mode must be 'open', 'save', or 'folder'")
    finally:
        root.destroy()