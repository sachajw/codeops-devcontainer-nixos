"""Constants and validation for the deploy script."""

import re
import sys
from pathlib import Path

MACHINE = sys.argv[1] if len(sys.argv) > 1 else "dev"
USER = "tvl"
DISTRO = "nixos"
MEMORY = "4G"
CPUS = "2"
DISK = "64G"
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIGS = ["configuration.nix", "home.nix"]
MAC_PATH = f"/mnt/mac{SCRIPT_DIR}"
HOME_MANAGER_URL = (
    "https://github.com/nix-community/home-manager/archive/release-25.05.tar.gz"
)
VALID_MACHINE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")


def validate_machine_name(name: str) -> None:
    """Validate machine name is safe for OrbStack.

    Args:
        name: Machine name to validate.

    Raises:
        TypeError: If name is not a string.
        ValueError: If the name is empty or contains invalid characters.
    """
    if not isinstance(name, str):
        raise TypeError(
            f"Machine name must be a string, got {type(name).__name__}"
        )
    if not name:
        raise ValueError("Machine name cannot be empty")
    if not VALID_MACHINE_RE.match(name):
        raise ValueError(
            f"Invalid machine name '{name}'. "
            "Must start with alphanumeric and contain only letters, digits, dots, dashes, underscores (max 64 chars)."
        )


def validate_config_files() -> None:
    """Verify all required config files exist locally.

    Raises:
        FileNotFoundError: If the script directory or any required config file is missing.
    """
    if not SCRIPT_DIR.is_dir():
        raise FileNotFoundError(
            f"Script directory does not exist: {SCRIPT_DIR}"
        )
    for config in CONFIGS:
        path = SCRIPT_DIR / config
        if not path.exists():
            raise FileNotFoundError(
                f"Required config file not found: {config}\n"
                f"Expected at: {path}"
            )
