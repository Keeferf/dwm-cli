"""Help menu – explains all watermarking techniques."""

from rich.panel import Panel

from dwm_cli.ui.console import console, wait_for_enter


def show_help_menu() -> None:
    """Display a detailed explanation of all watermarking methods."""
    console.clear()

    help_text = """
[bold yellow]1. Visible Watermarking[/]
   • Overlays text or a logo (image) directly on top of the image.
   • [green]Visible[/] to the human eye – ideal for branding and copyright notices.
   • Simple and fast, but can be cropped or obscured by editing.
   • Supports custom fonts, positions, opacity, and scaling.

[bold yellow]2. LSB Steganography[/]
   • Hides data in the [magenta]least significant bits[/] of each pixel's colour channels.
   • [green]Invisible[/] to the naked eye – perfect for covert communication.
   • The payload is spread pseudo‑randomly across the image using a secret key.
   • [red]Fragile:[/] lossy compression (JPEG) or resizing will destroy the hidden data.
   • Use for small text/JSON metadata when the image remains lossless (PNG, BMP).

[bold yellow]3. Hybrid Watermarking (DCT‑DWT‑QIM)[/]
   • Combines Discrete Cosine Transform, Discrete Wavelet Transform, and Quantization Index Modulation.
   • Embeds data in the frequency domain – [green]invisible[/] and [green]robust[/].
   • Withstands JPEG compression, scaling, and some filtering.
   • Slightly alters image quality (often imperceptible) but provides strong tamper resistance.
   • Ideal for digital rights management and forensic tracking.

[bold cyan]Configuration[/]
   All watermarking parameters (position, opacity, font, colour, etc.) are stored in
   configuration profiles. Use the [cyan]'Manage configurations'[/] menu to switch or create profiles.
    """

    console.print(
        Panel(
            help_text,
            title="[bold cyan]How the Watermarking Methods Work[/]",
            border_style="cyan",
            expand=False,
        )
    )

    console.print("\n[dim]Select a method from the main menu to start.[/]")
    wait_for_enter()
    console.clear()
