"""Prompt and workflow functions for DCT-DWT-QIM watermarking."""

from datetime import datetime
from pathlib import Path
from typing import List

from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt

from dwm_cli.core.hybrid_watermark import (
    NoPayloadError,
    decode_dct_dwt_qim,
    encode_dct_dwt_qim,
)
from dwm_cli.ui.console import console, wait_for_enter
from dwm_cli.utils.image_helpers import validate_image


def process_hybrid_encode_single(input_path: Path) -> None:
    """Encode metadata into a single image via DCT-DWT-QIM."""
    console.print(Panel("[bold]Hybrid Watermark – Encode[/]", style="cyan"))
    owner = Prompt.ask("Owner")
    project = Prompt.ask("Project")
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {"owner": owner, "project": project, "created": created}

    console.print(f"[dim]Embedding timestamp: {created}[/]")

    try:
        out = encode_dct_dwt_qim(input_path, payload, key=None)
        console.print(
            Panel(
                f"[bold green]✓ Hybrid watermark embedded:[/] {out}",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(Panel(f"[bold red]Error:[/] {e}", border_style="red"))
    wait_for_enter()


def process_hybrid_encode_batch(input_paths: List[Path]) -> None:
    """Encode metadata into multiple images via DCT-DWT-QIM."""
    valid_paths = [p for p in input_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]Hybrid Watermark – Batch Encode[/]", style="cyan"))
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
        task = progress.add_task("[cyan]Encoding hybrid...", total=len(valid_paths))
        for inp in valid_paths:
            try:
                encode_dct_dwt_qim(inp, payload, key=None)
                progress.update(task, advance=1, description=f"[green]✓ {inp.name}")
            except Exception as e:
                console.print(f"[red]Error on {inp.name}: {e}[/]")
                progress.update(
                    task, advance=1, description=f"[red]✗ {inp.name} failed"
                )
        progress.update(task, description="[bold green]Completed![/]")
    wait_for_enter()


def process_hybrid_decode_single(input_path: Path) -> None:
    """Extract payload from a single image via DCT-DWT-QIM."""
    console.print(Panel("[bold]Hybrid Watermark – Decode[/]", style="cyan"))
    try:
        payload = decode_dct_dwt_qim(input_path, key=None)
        console.print(
            Panel(
                f"[bold green]Extracted payload:[/]\n{payload}",
                border_style="green",
            )
        )
    except NoPayloadError as e:
        console.print(Panel(f"[yellow]ℹ {e}[/]", border_style="yellow"))
    except Exception as e:
        console.print(Panel(f"[bold red]Error:[/] {e}", border_style="red"))
    wait_for_enter()


def process_hybrid_decode_batch(input_paths: List[Path]) -> None:
    """Extract payload from multiple images via DCT-DWT-QIM."""
    valid_paths = [p for p in input_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]Hybrid Watermark – Batch Decode[/]", style="cyan"))

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Decoding hybrid...", total=len(valid_paths))
        for inp in valid_paths:
            try:
                payload = decode_dct_dwt_qim(inp, key=None)
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
