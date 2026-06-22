"""Bosscribe CLI — dead-simple audio transcription.

Usage:
    transcribe voice_note.opus              # print to terminal
    transcribe voice_note.opus --save       # save as .txt
    transcribe voice_note.opus --copy       # copy to clipboard
    transcribe voice_note.opus -l hi        # specify language
    transcribe config --show                # view settings
    transcribe config --save-to ~/notes     # set default save location
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from bosscribe import __version__
from bosscribe.config import (
    get_default_model,
    get_save_dir,
    set_default_model,
    set_save_dir,
    show_config,
)
from bosscribe.transcriber import transcribe, VALID_MODELS
from bosscribe.utils import (
    check_ffmpeg,
    copy_to_clipboard,
    get_output_path,
    validate_audio_file,
)

console = Console()


def _handle_config(args: argparse.Namespace) -> None:
    """Handle the 'config' subcommand."""
    if args.save_to is not None:
        set_save_dir(args.save_to)
    if args.model is not None:
        set_default_model(args.model)
    # Show config if --show is set, or if no other flags were given
    if args.show or (args.save_to is None and args.model is None):
        show_config()
        if Path("config").exists() and Path("config").is_file():
            console.print(
                "[dim]Note: A file named 'config' exists in this directory.[/dim]"
            )
            console.print(
                "[dim]If you wanted to transcribe it, "
                "use: [cyan]transcribe ./config[/cyan] instead.[/dim]\n"
            )


def _handle_transcribe(args: argparse.Namespace) -> None:
    """Handle the main transcription flow."""
    # Check ffmpeg
    if not check_ffmpeg():
        raise SystemExit(1)

    # Validate the audio file
    audio_path = validate_audio_file(args.audio_file)

    # Determine model
    model = args.model or get_default_model()

    # Transcribe with a nice spinner
    console.print()
    try:
        with console.status(
            f"[bold cyan]Transcribing[/bold cyan] [dim]{audio_path.name}[/dim] "
            f"[dim](model: {model})[/dim]",
            spinner="dots",
        ):
            text = transcribe(str(audio_path), model=model, language=args.language)
    except Exception as e:
        error_msg = str(e)
        if "Failed to load audio" in error_msg or "Invalid data" in error_msg:
            console.print(
                "\n[bold red]✗ Could not read the audio file.[/bold red]"
            )
            console.print(
                "  The file may be corrupted, empty,"
                " or in an unsupported codec."
            )
            console.print(
                "  Try converting it first: "
                "[cyan]ffmpeg -i input.opus output.wav[/cyan]\n"
            )
        else:
            console.print(
                f"\n[bold red]✗ Transcription failed:[/bold red]"
                f" {error_msg}\n"
            )
        raise SystemExit(1)

    if not text:
        console.print("[yellow]⚠ No speech detected in the audio file.[/yellow]")
        raise SystemExit(0)

    # Print to terminal (always, unless piped)
    if sys.stdout.isatty():
        console.print()
        console.print(Panel(
            text, title="📝 Transcription",
            border_style="green", padding=(1, 2),
        ))
        console.print()
    else:
        # When piped, output raw text (for `transcribe file.opus | pbcopy`)
        print(text)

    # Save to file if requested
    if args.save or args.output:
        if args.output:
            output_path = Path(args.output).expanduser().resolve()
        else:
            default_dir = get_save_dir()
            output_path = get_output_path(audio_path, default_dir)

        # Validate output path doesn't target a directory
        if output_path.exists() and output_path.is_dir():
            console.print(
                f"\n[bold red]✗ Cannot overwrite directory:[/bold red]"
                f" {output_path}"
            )
            raise SystemExit(1)

        # Create the parent directory if needed (catch bad paths here so a
        # write failure doesn't surprise the user after a slow transcription)
        parent = output_path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                console.print(
                    f"\n[bold red]✗ Cannot create output directory:"
                    f"[/bold red] {parent}"
                )
                console.print(f"  {e}")
                raise SystemExit(1)

        try:
            output_path.write_text(text, encoding="utf-8")
            console.print(f"[green]✓ Saved to:[/green] [bold]{output_path}[/bold]")
        except PermissionError:
            console.print(
                f"[bold red]✗ Permission denied:[/bold red]"
                f" Cannot write to {output_path.parent}"
            )
            console.print("  Check folder permissions or choose a different location.")
        except OSError as e:
            console.print(f"[bold red]✗ Could not save file:[/bold red] {e}")

    # Copy to clipboard if requested
    if args.copy:
        if copy_to_clipboard(text):
            console.print("[green]✓ Copied to clipboard![/green] Paste away. 📋")


def main() -> None:
    """Main entry point for the CLI."""
    # Handle SIGPIPE gracefully when output is piped to a closed process
    # (e.g., `transcribe file.opus | head` when head exits early)
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    try:
        # Manual routing: check if first arg is "config" subcommand
        # This avoids argparse subparsers conflicting with the positional audio_file
        if len(sys.argv) > 1 and sys.argv[1] == "config":
            _main_config()
        else:
            _main_transcribe()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelled.[/dim]")
        raise SystemExit(130)


def _main_config() -> None:
    """Parse and handle the 'config' subcommand."""
    parser = argparse.ArgumentParser(
        prog="transcribe config",
        description="⚙️  Configure default settings for Bosscribe.",
    )
    parser.add_argument(
        "--save-to",
        metavar="PATH",
        default=None,
        help='Set default save location. Use "" to clear.',
    )
    parser.add_argument(
        "--model",
        metavar="MODEL",
        default=None,
        choices=sorted(VALID_MODELS),
        help=(
            "Set default Whisper model "
            "(tiny/base/small/medium/large-v3/large-v3-turbo)."
        ),
    )
    parser.add_argument(
        "--show",
        action="store_true",
        default=False,
        help="Show current configuration.",
    )

    args = parser.parse_args(sys.argv[2:])  # Skip ['transcribe', 'config']
    _handle_config(args)


def _main_transcribe() -> None:
    """Parse and handle the main transcription command."""
    parser = argparse.ArgumentParser(
        prog="transcribe",
        description=(
            "🎙️  Bosscribe — Dead-simple audio transcription."
            " Just transcribe it."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  transcribe voice_note.opus              Transcribe & print to terminal\n"
            "  transcribe voice_note.opus --save       Save as voice_note.txt\n"
            "  transcribe voice_note.opus --copy       Copy to clipboard\n"
            "  transcribe voice_note.opus -l hi        Transcribe Hindi audio\n"
            "  transcribe voice_note.opus -m large-v3  Use the large model\n"
            "  transcribe config --save-to ~/notes     Set default save location\n"
            "  transcribe config --show                View settings\n"
        ),
    )
    parser.add_argument(
        "audio_file",
        nargs="?",
        help="Path to the audio file to transcribe.",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"bosscribe {__version__}",
    )
    parser.add_argument(
        "-s", "--save",
        action="store_true",
        default=False,
        help="Save transcription as a .txt file.",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        default=None,
        help="Save to a specific file path (implies --save).",
    )
    parser.add_argument(
        "-c", "--copy",
        action="store_true",
        default=False,
        help="Copy transcription to clipboard.",
    )
    parser.add_argument(
        "-m", "--model",
        metavar="MODEL",
        default=None,
        choices=sorted(VALID_MODELS),
        help=(
            "Whisper model to use (default: base). "
            "Options: tiny, base, small, medium, large-v3."
        ),
    )
    parser.add_argument(
        "-l", "--language",
        metavar="LANG",
        default=None,
        help=(
            "Language code for transcription (e.g., en, hi, es). "
            "Auto-detects if not set."
        ),
    )

    args = parser.parse_args()

    if args.audio_file:
        _handle_transcribe(args)
    else:
        parser.print_help()
        raise SystemExit(0)


if __name__ == "__main__":
    main()
