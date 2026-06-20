"""Prompt and workflow functions for Hybrid (DWT+DCT+QIM) watermarking."""

from datetime import datetime
from pathlib import Path
from typing import List

from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt

from dwm_cli.core.hybrid_watermark import (
    calculate_capacity,
    embed_watermark,
    encode_payload,
    extract_watermark,
    validate_capacity,
)
from dwm_cli.ui.console import console, wait_for_enter
from dwm_cli.utils.image_helpers import validate_image


def _build_payload(owner: str, project: str, created: str) -> str:
    """Build the canonical UTF-8 payload string for hybrid watermarking.

    Args:
        owner: Name of the owner.
        project: Project identifier.
        created: ISO-like timestamp string.

    Returns:
        Formatted payload string.
    """
    return f"Owner: {owner}\nProject: {project}\nCreated: {created}"


def _get_output_path(input_path: Path) -> Path:
    """Generate a default output path for a watermarked image.

    Args:
        input_path: Original image path.

    Returns:
        Path with ``_wm`` suffix inserted before the extension.
    """
    return input_path.parent / f"{input_path.stem}_wm{input_path.suffix}"


# ---------------------------------------------------------------------------
# Encode workflows
# ---------------------------------------------------------------------------


def process_hybrid_encode_single(input_path: Path) -> None:
    """Encode a robust invisible watermark into a single image.

    Prompts the user for owner and project metadata, embeds the payload
    using DWT+DCT+QIM, and saves the result next to the source file.
    """
    console.print(Panel("[bold]Hybrid Watermarking – Encode[/]", style="magenta"))

    owner = Prompt.ask("Owner")
    project = Prompt.ask("Project")
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = _build_payload(owner, project, created)

    console.print(
        f"[dim]Embedding payload ({len(payload.encode('utf-8'))} bytes) at {created}[/]"
    )

    out_path = _get_output_path(input_path)

    try:
        embed_watermark(str(input_path), str(out_path), payload)
        console.print(
            Panel(
                f"[bold green]✓ Hybrid watermark embedded:[/] {out_path}",
                border_style="green",
            )
        )
    except ValueError as exc:
        console.print(
            Panel(f"[bold red]Validation Error:[/] {exc}", border_style="red")
        )
    except Exception as exc:
        console.print(Panel(f"[bold red]Error:[/] {exc}", border_style="red"))

    wait_for_enter()


def process_hybrid_encode_batch(input_paths: List[Path]) -> None:
    """Encode robust invisible watermarks into multiple images.

    Prompts once for owner and project metadata, then embeds the same
    payload into every valid image in the batch.
    """
    valid_paths = [p for p in input_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]Hybrid Watermarking – Batch Encode[/]", style="magenta"))

    owner = Prompt.ask("Owner")
    project = Prompt.ask("Project")
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = _build_payload(owner, project, created)

    console.print(
        f"[dim]Embedding payload ({len(payload.encode('utf-8'))} bytes) for all images at {created}[/]"
    )

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[magenta]Encoding hybrid...", total=len(valid_paths))

        for inp in valid_paths:
            out_path = _get_output_path(inp)
            try:
                embed_watermark(str(inp), str(out_path), payload)
                progress.update(task, advance=1, description=f"[green]✓ {inp.name}")
            except ValueError as exc:
                console.print(f"[yellow]⚠ {inp.name}: {exc}[/]")
                progress.update(
                    task, advance=1, description=f"[yellow]⚠ {inp.name} (skipped)"
                )
            except Exception as exc:
                console.print(f"[red]Error on {inp.name}: {exc}[/]")
                progress.update(
                    task, advance=1, description=f"[red]✗ {inp.name} failed"
                )

        progress.update(task, description="[bold green]Completed![/]")

    wait_for_enter()


# ---------------------------------------------------------------------------
# Decode workflows
# ---------------------------------------------------------------------------


def process_hybrid_decode_single(input_path: Path) -> None:
    """Extract a robust invisible watermark from a single image.

    Uses the DWT+DCT+QIM extraction pipeline with confidence-based
    redundant recovery from LH and HL sub-bands.
    """
    console.print(Panel("[bold]Hybrid Watermarking – Decode[/]", style="magenta"))

    try:
        payload = extract_watermark(str(input_path))
        console.print(
            Panel(
                f"[bold green]Extracted payload:[/]\n{payload}",
                border_style="green",
            )
        )
    except ValueError as exc:
        console.print(Panel(f"[yellow]ℹ {exc}[/]", border_style="yellow"))
    except Exception as exc:
        console.print(Panel(f"[bold red]Error:[/] {exc}", border_style="red"))

    wait_for_enter()


def process_hybrid_decode_batch(input_paths: List[Path]) -> None:
    """Extract robust invisible watermarks from multiple images.

    Processes each image independently and reports results.
    """
    valid_paths = [p for p in input_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]Hybrid Watermarking – Batch Decode[/]", style="magenta"))

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[magenta]Decoding hybrid...", total=len(valid_paths))

        for inp in valid_paths:
            try:
                payload = extract_watermark(str(inp))
                console.print(
                    Panel(
                        f"[bold green]{inp.name}[/] payload:\n{payload}",
                        border_style="green",
                    )
                )
                progress.update(task, advance=1, description=f"[green]✓ {inp.name}")
            except ValueError as exc:
                console.print(f"[yellow]{inp.name}: {exc}[/]")
                progress.update(
                    task,
                    advance=1,
                    description=f"[yellow]⚠ {inp.name} (no payload)",
                )
            except Exception as exc:
                console.print(f"[red]Error on {inp.name}: {exc}[/]")
                progress.update(
                    task, advance=1, description=f"[red]✗ {inp.name} failed"
                )

        progress.update(task, description="[bold green]Completed![/]")

    wait_for_enter()
