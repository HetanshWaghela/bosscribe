"""Persistent user configuration for Bosscribe.

Config is stored as a simple JSON file at:
  - macOS:   ~/Library/Application Support/bosscribe/config.json
  - Linux:   ~/.config/bosscribe/config.json
  - Windows: C:\\Users\\<user>\\AppData\\Local\\bosscribe\\config.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from platformdirs import user_config_dir
from rich.console import Console
from rich.table import Table

from bosscribe.transcriber import VALID_MODELS

CONFIG_DIR = Path(user_config_dir("bosscribe", ensure_exists=True))
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default configuration values
DEFAULTS = {
    "default_save_dir": "",
    "default_model": "base",
}

console = Console()


def load_config() -> dict:
    """Load config from disk. Returns defaults if no config file exists."""
    config = DEFAULTS.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            # Only accept known keys to prevent config tampering
            for key in DEFAULTS:
                if key in saved and isinstance(saved[key], str):
                    config[key] = saved[key]
                elif key in saved:
                    # Non-string value — skip it, use default
                    pass
            # Ensure model is valid, otherwise fallback to default
            if config["default_model"] not in VALID_MODELS:
                config["default_model"] = DEFAULTS["default_model"]
        except (json.JSONDecodeError, OSError, TypeError):
            # Corrupted config — just use defaults
            pass
    return config


def save_config(config: dict) -> None:
    """Save config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_save_dir() -> Optional[str]:
    """Get the configured default save directory, or None if not set."""
    config = load_config()
    save_dir = config.get("default_save_dir", "")
    return save_dir if save_dir else None


def set_save_dir(path: str) -> None:
    """Set or clear the default save directory."""
    config = load_config()
    if path and path.strip():
        # Expand ~ and resolve to absolute path
        resolved = Path(path).expanduser().resolve()
        # Validate the directory exists or can be created
        if resolved.exists():
            if not resolved.is_dir():
                console.print(f"[bold red]✗ Not a directory:[/bold red] {resolved}")
                raise SystemExit(1)
            if not os.access(str(resolved), os.W_OK):
                console.print(f"[bold red]✗ No write permission:[/bold red] {resolved}")
                console.print("  Choose a directory you have write access to.")
                raise SystemExit(1)
        else:
            # Check closest existing ancestor directory for write permission
            parent = resolved
            while not parent.exists():
                parent = parent.parent
            if not os.access(str(parent), os.W_OK):
                console.print(
                    f"[bold red]✗ Cannot write to directory:[/bold red]"
                    f" {resolved}"
                )
                console.print(
                    f"  Parent directory [bold]{parent}[/bold]"
                    " is not writable."
                )
                raise SystemExit(1)
        config["default_save_dir"] = str(resolved)
        console.print(
            f"[green]✓[/green] Default save location set to:"
            f" [bold]{resolved}[/bold]"
        )
    else:
        config["default_save_dir"] = ""
        console.print(
            "[green]✓[/green] Default save location cleared."
            " Files will save next to audio."
        )
    save_config(config)


def get_default_model() -> str:
    """Get the configured default model."""
    config = load_config()
    return config.get("default_model", "base")


def set_default_model(model: str) -> None:
    """Set the default whisper model."""
    if model not in VALID_MODELS:
        console.print(f"[bold red]✗ Unknown model:[/bold red] {model}")
        console.print(f"  Valid models: {', '.join(sorted(VALID_MODELS))}")
        raise SystemExit(1)
    config = load_config()
    config["default_model"] = model
    save_config(config)
    console.print(f"[green]✓[/green] Default model set to: [bold]{model}[/bold]")


def show_config() -> None:
    """Pretty-print current configuration."""
    config = load_config()

    table = Table(
        title="⚙️  Bosscribe Config",
        show_header=True, header_style="bold cyan",
    )
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    save_dir = config.get("default_save_dir", "")
    table.add_row(
        "Default save location",
        save_dir if save_dir else "[dim]Not set (saves next to audio file)[/dim]",
    )
    table.add_row("Default model", config.get("default_model", "base"))
    table.add_row("Config file", str(CONFIG_FILE))

    console.print()
    console.print(table)
    console.print()
