"""File selection dialog abstraction using tkinter."""

from pathlib import Path
from typing import Optional, Union, List


def select_file_dialog(
    title: str,
    filetypes: list,
    mode: str = "open",
    multiple: bool = False
) -> Optional[Union[Path, List[Path]]]:
    """
    Open a file/folder selection dialog using tkinter.
    
    Args:
        title: Dialog window title
        filetypes: List of tuples like [("Image files", "*.jpg *.png")]
        mode: "open", "save", or "folder"
        multiple: If True, allow multi-select (only for mode="open")
    
    Returns:
        Path object, list of Path objects, or None if cancelled
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