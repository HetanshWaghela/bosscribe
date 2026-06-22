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


def _detect_ffmpeg_installer() -> Optional[tuple[str, list[str]]]:
    """Find an available package manager and the command to install ffmpeg.

    Returns (label, command) or None if no known package manager is found.
    """
    if sys.platform == "darwin":
        if shutil.which("brew"):
            return ("Homebrew", ["brew", "install", "ffmpeg"])
    elif sys.platform == "win32":
        if shutil.which("winget"):
            return ("winget", ["winget", "install", "--id", "Gyan.FFmpeg", "-e"])
        if shutil.which("choco"):
            return ("Chocolatey", ["choco", "install", "ffmpeg", "-y"])
    else:
        if shutil.which("apt-get"):
            return ("apt", ["sudo", "apt-get", "install", "-y", "ffmpeg"])
        if shutil.which("dnf"):
            return ("dnf", ["sudo", "dnf", "install", "-y", "ffmpeg"])
        if shutil.which("pacman"):
            return ("pacman", ["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"])
        if shutil.which("zypper"):
            return ("zypper", ["sudo", "zypper", "install", "-y", "ffmpeg"])
    return None


def _print_manual_ffmpeg_instructions() -> None:
    """Print platform-specific manual install instructions for ffmpeg."""
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


def check_ffmpeg(auto_install: bool = True) -> bool:
    """Check if ffmpeg is installed; offer to install it if missing.

    When ffmpeg is absent and we're running interactively, detect the system
    package manager and offer to install ffmpeg automatically. Falls back to
    printing manual instructions if the user declines, no package manager is
    found, or we're not in a terminal.
    """
    if shutil.which("ffmpeg") is not None:
        return True

    console.print("\n[bold red]✗ FFmpeg isn't installed.[/bold red]")
    console.print("  Bosscribe needs FFmpeg to read audio files.\n")

    installer = _detect_ffmpeg_installer()

    # Only offer to auto-install when we have a package manager AND a terminal
    # to prompt in (don't hang or guess when piped/scripted).
    if auto_install and installer is not None and sys.stdin.isatty():
        label, cmd = installer
        console.print(f"  Bosscribe can install it for you via {label}:")
        console.print(f"    [cyan]{' '.join(cmd)}[/cyan]\n")
        try:
            answer = input("  Install FFmpeg now? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print()
            answer = "n"

        if answer in ("", "y", "yes"):
            console.print(f"\n[cyan]Installing FFmpeg via {label}…[/cyan]\n")
            try:
                result = subprocess.run(cmd)
            except OSError as e:
                console.print(
                    f"[bold red]✗ Couldn't run the installer:[/bold red] {e}\n"
                )
                _print_manual_ffmpeg_instructions()
                return False
            if result.returncode == 0 and shutil.which("ffmpeg") is not None:
                console.print("\n[green]✓ FFmpeg installed! Carrying on.[/green]")
                return True
            console.print(
                "\n[bold red]✗ FFmpeg install didn't complete.[/bold red]"
                " Try installing it manually:\n"
            )
            _print_manual_ffmpeg_instructions()
            return False

        # User declined — show manual instructions
        console.print()

    _print_manual_ffmpeg_instructions()
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
