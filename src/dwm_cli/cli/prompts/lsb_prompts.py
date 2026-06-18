"""Prompt and workflow functions for LSB steganography."""

from datetime import datetime
from pathlib import Path
from typing import List

from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt

from dwm_cli.core.lsb_watermark import NoPayloadError, decode_lsb, encode_lsb
from dwm_cli.ui.console import console, wait_for_enter
from dwm_cli.utils.image_helpers import validate_image


def process_lsb_encode_single(input_path: Path) -> None:
    """Encode metadata into a single image via LSB."""
    console.print(Panel("[bold]LSB Steganography – Encode[/]", style="cyan"))
    owner = Prompt.ask("Owner")
    project = Prompt.ask("Project")
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {"owner": owner, "project": project, "created": created}

    console.print(f"[dim]Embedding timestamp: {created}[/]")

    try:
        out = encode_lsb(input_path, payload, None)
        console.print(
            Panel(
                f"[bold green]✓ LSB watermark embedded:[/] {out}", border_style="green"
            )
        )
    except Exception as e:
        console.print(Panel(f"[bold red]Error:[/] {e}", border_style="red"))
    wait_for_enter()


def process_lsb_encode_batch(input_paths: List[Path]) -> None:
    """Encode metadata into multiple images via LSB."""
    valid_paths = [p for p in input_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]LSB Steganography – Batch Encode[/]", style="cyan"))
    owner = Prompt.ask("Owner")
    project = Prompt.ask("Project")
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {"owner": owner, "project": project, "created": created}

    console.print(f"[dim]Embedding timestamp: {created} for all images[/]")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Encoding LSB...", total=len(valid_paths))
        for inp in valid_paths:
            try:
                encode_lsb(inp, payload, None)
                progress.update(task, advance=1, description=f"[green]✓ {inp.name}")
            except Exception as e:
                console.print(f"[red]Error on {inp.name}: {e}[/]")
                progress.update(
                    task, advance=1, description=f"[red]✗ {inp.name} failed"
                )
        progress.update(task, description="[bold green]Completed![/]")
    wait_for_enter()


def process_lsb_decode_single(input_path: Path) -> None:
    """Extract LSB payload from a single image."""
    console.print(Panel("[bold]LSB Steganography – Decode[/]", style="cyan"))
    try:
        payload = decode_lsb(input_path)
        console.print(
            Panel(f"[bold green]Extracted payload:[/]\n{payload}", border_style="green")
        )
    except NoPayloadError as e:
        console.print(Panel(f"[yellow]ℹ {e}[/]", border_style="yellow"))
    except Exception as e:
        console.print(Panel(f"[bold red]Error:[/] {e}", border_style="red"))
    wait_for_enter()


def process_lsb_decode_batch(input_paths: List[Path]) -> None:
    """Extract LSB payload from multiple images."""
    valid_paths = [p for p in input_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]LSB Steganography – Batch Decode[/]", style="cyan"))

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Decoding LSB...", total=len(valid_paths))
        for inp in valid_paths:
            try:
                payload = decode_lsb(inp)
                console.print(
                    Panel(
                        f"[bold green]{inp.name}[/] payload:\n{payload}",
                        border_style="green",
                    )
                )
                progress.update(task, advance=1, description=f"[green]✓ {inp.name}")
            except NoPayloadError as e:
                console.print(f"[yellow]{inp.name}: {e}[/]")
                progress.update(
                    task, advance=1, description=f"[yellow]⚠ {inp.name} (no payload)"
                )
            except Exception as e:
                console.print(f"[red]Error on {inp.name}: {e}[/]")
                progress.update(
                    task, advance=1, description=f"[red]✗ {inp.name} failed"
                )
        progress.update(task, description="[bold green]Completed![/]")
    wait_for_enter()
