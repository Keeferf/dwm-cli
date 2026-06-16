from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt

from dwm_cli.cli.helpers import color_to_rgb, get_output_dir
from dwm_cli.config.settings import get_current_profile_name, load_config
from dwm_cli.core.visible_watermark import add_image_watermark, add_text_watermark
from dwm_cli.ui.console import console, display_info_table, wait_for_enter
from dwm_cli.utils.image_helpers import validate_image

# ------------------------------------------------------------
# Original prompt functions (kept for compatibility)
# ------------------------------------------------------------


@dataclass
class WatermarkSettings:
    """All watermark settings loaded from the current profile."""

    position: str
    opacity: float
    font_path: Optional[str]
    font_size: int
    text_color: Tuple[int, int, int]
    scale: float
    output_dir: Path


def get_watermark_settings() -> WatermarkSettings:
    """Load and validate watermark settings from the current profile."""
    config = load_config()
    font_path = config.get("font", "") or None
    if font_path and not Path(font_path).exists():
        console.print(
            f"[yellow]Font file '{font_path}' not found, using PIL default.[/]"
        )
        font_path = None

    return WatermarkSettings(
        position=config.get("position", "bottom-right"),
        opacity=float(config.get("opacity", 0.5)),
        font_path=font_path,
        font_size=int(config.get("font_size", 36)),
        text_color=color_to_rgb(config.get("text_color", "white")),
        scale=float(config.get("scale", 1.0)),
        output_dir=get_output_dir(),
    )


def process_text_watermark_single(input_path: Path) -> None:
    """Apply text watermark to a single image."""
    console.print(Panel("[bold]Text Watermark (Single Image)[/]", style="cyan"))
    settings = get_watermark_settings()
    display_info_table(load_config(), settings.output_dir, get_current_profile_name())

    output_path = (
        settings.output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"
    )
    text = Prompt.ask("Watermark text")

    try:
        add_text_watermark(
            input_path=input_path,
            output_path=output_path,
            text=text,
            position=settings.position,
            font_path=settings.font_path,
            font_size=settings.font_size,
            opacity=settings.opacity,
            text_color=settings.text_color,
        )
        console.print(
            Panel(
                f"[bold green]✓ Text watermark added:[/] {output_path}",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(Panel(f"[bold red]Error:[/] {e}", border_style="red"))
    wait_for_enter()


def process_text_watermark_batch(input_paths: List[Path]) -> None:
    """Apply text watermark to a list of images (batch)."""
    valid_paths = [p for p in input_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]Batch Text Watermark[/]", style="cyan"))
    settings = get_watermark_settings()
    display_info_table(load_config(), settings.output_dir, get_current_profile_name())

    text = Prompt.ask("Watermark text")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task(
            "[cyan]Applying text watermark...", total=len(valid_paths)
        )
        for input_path in valid_paths:
            output_path = (
                settings.output_dir
                / f"{input_path.stem}_watermarked{input_path.suffix}"
            )
            try:
                add_text_watermark(
                    input_path=input_path,
                    output_path=output_path,
                    text=text,
                    position=settings.position,
                    font_path=settings.font_path,
                    font_size=settings.font_size,
                    opacity=settings.opacity,
                    text_color=settings.text_color,
                )
                progress.update(
                    task, advance=1, description=f"[green]✓ {input_path.name}"
                )
            except Exception as e:
                console.print(f"[red]Error on {input_path.name}: {e}[/]")
                progress.update(
                    task, advance=1, description=f"[red]✗ {input_path.name} failed"
                )
        progress.update(task, description="[bold green]Completed![/]")
    wait_for_enter()


def process_image_watermark_single(source_path: Path, watermark_path: Path) -> None:
    """Apply image watermark to a single image."""
    console.print(Panel("[bold]Image Watermark (Single Image)[/]", style="cyan"))
    settings = get_watermark_settings()
    display_info_table(load_config(), settings.output_dir, get_current_profile_name())

    output_path = (
        settings.output_dir / f"{source_path.stem}_watermarked{source_path.suffix}"
    )

    try:
        add_image_watermark(
            input_path=source_path,
            output_path=output_path,
            watermark_path=watermark_path,
            position=settings.position,
            scale=settings.scale,
            opacity=settings.opacity,
        )
        console.print(
            Panel(
                f"[bold green]✓ Image watermark added:[/] {output_path}",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(Panel(f"[bold red]Error:[/] {e}", border_style="red"))
    wait_for_enter()


def process_image_watermark_batch(
    source_paths: List[Path], watermark_path: Path
) -> None:
    """Apply image watermark to a list of images."""
    valid_paths = [p for p in source_paths if validate_image(p)]
    if not valid_paths:
        console.print("[red]No valid source images to process.[/]")
        wait_for_enter()
        return

    console.print(Panel("[bold]Batch Image Watermark[/]", style="cyan"))
    settings = get_watermark_settings()
    display_info_table(load_config(), settings.output_dir, get_current_profile_name())

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task(
            "[cyan]Applying image watermark...", total=len(valid_paths)
        )
        for source_path in valid_paths:
            output_path = (
                settings.output_dir
                / f"{source_path.stem}_watermarked{source_path.suffix}"
            )
            try:
                add_image_watermark(
                    input_path=source_path,
                    output_path=output_path,
                    watermark_path=watermark_path,
                    position=settings.position,
                    scale=settings.scale,
                    opacity=settings.opacity,
                )
                progress.update(
                    task, advance=1, description=f"[green]✓ {source_path.name}"
                )
            except Exception as e:
                console.print(f"[red]Error on {source_path.name}: {e}[/]")
                progress.update(
                    task, advance=1, description=f"[red]✗ {source_path.name} failed"
                )
        progress.update(task, description="[bold green]Completed![/]")
    wait_for_enter()
