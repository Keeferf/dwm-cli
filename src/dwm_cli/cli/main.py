"""
Digital Watermarking CLI - Main Entry Point

This is the CLI entry point using Typer. It delegates to the menu system
which handles all interactive prompts and workflows.
"""

import typer

from dwm_cli.cli.menus.main_menu import show_main_menu

app = typer.Typer(help="Watermarking CLI Tool", no_args_is_help=False)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Interactive menu for watermarking tool. Run without arguments."""
    if ctx.invoked_subcommand is not None:
        return

    show_main_menu()


if __name__ == "__main__":
    app()