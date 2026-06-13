"""Watermark-specific prompts and workflows."""

from pathlib import Path
from typing import List
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

from digital_watermarking_cli.core.visible_watermark import add_text_watermark, add_image_watermark
from digital_watermarking_cli.utils.image_helpers import validate_image
from digital_watermarking_cli.ui.console import console
from digital_watermarking_cli.cli.helpers import (
    get_current_config,
    get_output_dir,
    color_to_rgb,
    get_default_font_path
)
from digital_watermarking_cli.cli.prompts.file_prompts import get_input_paths_interactive


def prompt_text_watermark() -> None:
    """Interactive prompt for single image text watermark."""
    console.print(Panel("[bold]Text Watermark (Single Image)[/]", style="cyan"))
    
    # Display current profile info
    from digital_watermarking_cli.ui.console import display_info_table
    from digital_watermarking_cli.config.settings import get_current_profile_name
    config = get_current_config()
    display_info_table(config, get_output_dir(), get_current_profile_name())

    input_path = get_input_paths_interactive(
        "Source image to watermark",
        [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
    )[0]
    
    output_dir = get_output_dir()
    output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"

    config = get_current_config()
    text = Prompt.ask("Watermark text")

    position = config.get("position", "bottom-right")
    font_path = config.get("font", "") or None
    
    if font_path and not Path(font_path).exists():
        console.print(f"[yellow]Font file '{font_path}' not found, using PIL default.[/]")
        font_path = None
    
    font_size = config.get("font_size", 36)
    opacity = config.get("opacity", 0.5)
    text_color_str = config.get("text_color", "white")
    text_color = color_to_rgb(text_color_str)

    try:
        add_text_watermark(
            input_path=input_path,
            output_path=output_path,
            text=text,
            position=position,
            font_path=font_path,
            font_size=int(font_size),
            opacity=float(opacity),
            text_color=text_color,
        )
        console.print(f"[bold green]✓ Text watermark added:[/] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")


def prompt_text_watermark_batch(input_paths: List[Path]) -> None:
    """Interactive prompt for batch text watermark on multiple images."""
    # Validate all paths
    valid_paths = []
    for p in input_paths:
        if validate_image(p):
            valid_paths.append(p)
        else:
            console.print(f"[red]Skipping invalid/corrupt image: {p.name}[/]")

    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        return

    console.print(Panel("[bold]Batch Text Watermark[/]", style="cyan"))
    
    from digital_watermarking_cli.ui.console import display_info_table
    from digital_watermarking_cli.config.settings import get_current_profile_name
    config = get_current_config()
    display_info_table(config, get_output_dir(), get_current_profile_name())

    output_dir = get_output_dir()
    text = Prompt.ask("Watermark text")

    position = config.get("position", "bottom-right")
    font_path = config.get("font", "") or None
    
    if font_path and not Path(font_path).exists():
        console.print(f"[yellow]Font file '{font_path}' not found, using PIL default.[/]")
        font_path = None
    
    font_size = config.get("font_size", 36)
    opacity = config.get("opacity", 0.5)
    text_color_str = config.get("text_color", "white")
    text_color = color_to_rgb(text_color_str)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Applying text watermark...", total=len(valid_paths))
        for input_path in valid_paths:
            output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"
            try:
                add_text_watermark(
                    input_path=input_path,
                    output_path=output_path,
                    text=text,
                    position=position,
                    font_path=font_path,
                    font_size=int(font_size),
                    opacity=float(opacity),
                    text_color=text_color,
                )
                progress.update(task, advance=1, description=f"[green]✓ {input_path.name}")
            except Exception as e:
                console.print(f"[red]Error on {input_path.name}: {e}[/]")
                progress.update(task, advance=1, description=f"[red]✗ {input_path.name} failed")
    
    console.print("[bold green]Batch text watermarking completed![/]")


def prompt_image_watermark() -> None:
    """Interactive prompt for single image watermark."""
    console.print(Panel("[bold]Image Watermark (Single Image)[/]", style="cyan"))
    
    from digital_watermarking_cli.ui.console import display_info_table
    from digital_watermarking_cli.config.settings import get_current_profile_name
    config = get_current_config()
    display_info_table(config, get_output_dir(), get_current_profile_name())

    input_path = get_input_paths_interactive(
        "Source image to watermark",
        [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
    )[0]
    
    output_dir = get_output_dir()
    output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"

    watermark_path = get_input_paths_interactive(
        "Watermark image (logo)",
        [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif")]
    )[0]

    if not validate_image(watermark_path):
        console.print(f"[red]Watermark image is invalid or corrupted: {watermark_path}[/]")
        return

    config = get_current_config()
    position = config.get("position", "bottom-right")
    scale = config.get("scale", 1.0)
    opacity = config.get("opacity", 0.5)

    try:
        add_image_watermark(
            input_path=input_path,
            output_path=output_path,
            watermark_path=watermark_path,
            position=position,
            scale=float(scale),
            opacity=float(opacity),
        )
        console.print(f"[bold green]✓ Image watermark added:[/] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")


def prompt_image_watermark_batch(input_paths: List[Path]) -> None:
    """Interactive prompt for batch image watermark on multiple images."""
    # Validate all paths
    valid_paths = []
    for p in input_paths:
        if validate_image(p):
            valid_paths.append(p)
        else:
            console.print(f"[red]Skipping invalid/corrupt image: {p.name}[/]")

    if not valid_paths:
        console.print("[red]No valid images to process.[/]")
        return

    console.print(Panel("[bold]Batch Image Watermark[/]", style="cyan"))
    
    from digital_watermarking_cli.ui.console import display_info_table
    from digital_watermarking_cli.config.settings import get_current_profile_name
    config = get_current_config()
    display_info_table(config, get_output_dir(), get_current_profile_name())

    output_dir = get_output_dir()
    watermark_path = get_input_paths_interactive(
        "Watermark image (logo)",
        [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif")]
    )[0]

    if not validate_image(watermark_path):
        console.print(f"[red]Watermark image is invalid or corrupted: {watermark_path}[/]")
        return

    config = get_current_config()
    position = config.get("position", "bottom-right")
    scale = config.get("scale", 1.0)
    opacity = config.get("opacity", 0.5)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Applying image watermark...", total=len(valid_paths))
        for input_path in valid_paths:
            output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"
            try:
                add_image_watermark(
                    input_path=input_path,
                    output_path=output_path,
                    watermark_path=watermark_path,
                    position=position,
                    scale=float(scale),
                    opacity=float(opacity),
                )
                progress.update(task, advance=1, description=f"[green]✓ {input_path.name}")
            except Exception as e:
                console.print(f"[red]Error on {input_path.name}: {e}[/]")
                progress.update(task, advance=1, description=f"[red]✗ {input_path.name} failed")
    
    console.print("[bold green]Batch image watermarking completed![/]")