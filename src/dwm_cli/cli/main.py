"""
Digital Watermarking CLI - Main Entry Point

This is the CLI entry point using Typer. It delegates to the menu system
which handles all interactive prompts and workflows.
"""

import typer

from dwm_cli.cli.menus.main_menu import show_main_menu
from dwm_cli.ui.console import console

app = typer.Typer(help="Watermarking CLI Tool", no_args_is_help=False)


def _safe_run() -> None:
    """Run the interactive menu, converting interrupts/errors into clean exits."""
    try:
        show_main_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted - goodbye.[/]")
        raise typer.Exit(130)
    except Exception:
        console.print_exception(show_locals=False)
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Interactive menu for watermarking tool. Run without arguments."""
    if ctx.invoked_subcommand is not None:
        return

    _safe_run()


if __name__ == "__main__":
    app()