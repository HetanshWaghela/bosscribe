"""Utility functions for Bosscribe — ffmpeg check, file validation, clipboard."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()

# Audio formats that ffmpeg/whisper can handle
SUPPORTED_EXTENSIONS = {
    ".opus", ".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac",
    ".aac", ".wma", ".mp4", ".mpeg", ".mpga", ".oga", ".mka", ".wv",
}


def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed. Shows install instructions if not."""
    if shutil.which("ffmpeg") is not None:
        return True

    console.print("\n[bold red]✗ FFmpeg is not installed![/bold red]")
    console.print("  Bosscribe needs FFmpeg to process audio files.\n")

    if sys.platform == "darwin":
        console.print("  [bold]Install on macOS:[/bold]")
        console.print("    [cyan]brew install ffmpeg[/cyan]\n")
    elif sys.platform == "win32":
        console.print("  [bold]Install on Windows:[/bold]")
        console.print("    [cyan]choco install ffmpeg[/cyan]")
        console.print("    or [cyan]winget install ffmpeg[/cyan]\n")
    else:
        console.print("  [bold]Install on Linux:[/bold]")
        console.print("    [cyan]sudo apt install ffmpeg[/cyan]  (Debian/Ubuntu)")
        console.print("    [cyan]sudo dnf install ffmpeg[/cyan]  (Fedora)")
        console.print("    [cyan]sudo pacman -S ffmpeg[/cyan]    (Arch)\n")

    return False


def validate_audio_file(file_path: str) -> Path:
    """Validate that the audio file exists and has a supported extension.

    Returns the resolved Path, or raises SystemExit with a helpful message.
    """
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        console.print(f"\n[bold red]✗ File not found:[/bold red] {file_path}")
        console.print("  Double-check the path and try again.\n")
        raise SystemExit(1)

    if not path.is_file():
        console.print(f"\n[bold red]✗ Not a file:[/bold red] {file_path}")
        raise SystemExit(1)

    if not os.access(str(path), os.R_OK):
        console.print(
            f"\n[bold red]✗ Permission denied:[/bold red]"
            f" Cannot read the file: {file_path}"
        )
        console.print("  Check file permissions and try again.\n")
        raise SystemExit(1)

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        console.print(f"\n[bold red]✗ Unsupported format:[/bold red] {ext}")
        console.print(f"  Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}\n")
        raise SystemExit(1)

    return path


def get_output_path(audio_path: Path, default_save_dir: Optional[str] = None) -> Path:
    """Generate the output .txt path for a transcription.

    If a default_save_dir is configured, saves there.
    Otherwise, saves next to the audio file.
    """
    txt_name = audio_path.stem + ".txt"

    if default_save_dir:
        save_dir = Path(default_save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir / txt_name

    return audio_path.parent / txt_name


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard. Cross-platform.

    Returns True if successful, False otherwise.
    """
    try:
        if sys.platform == "darwin":
            process = subprocess.Popen(
                ["pbcopy"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
        elif sys.platform == "win32":
            process = subprocess.Popen(
                ["clip"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
            process.communicate(text.encode("utf-16le"))
            return process.returncode == 0
        else:
            # Linux — try xclip first, then xsel
            for cmd in [
                ["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
            ]:
                if shutil.which(cmd[0]):
                    process = subprocess.Popen(
                        cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    )
                    process.communicate(text.encode("utf-8"))
                    if process.returncode == 0:
                        return True
            console.print(
                "[yellow]⚠ Clipboard not available.[/yellow]"
                " Install xclip or xsel."
            )
            return False
    except OSError:
        console.print("[yellow]⚠ Could not copy to clipboard.[/yellow]")
        return False
