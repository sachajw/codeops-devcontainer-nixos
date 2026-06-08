#!/usr/bin/env python3
"""Deploy codeops NixOS dev environment to an OrbStack machine."""

import re
import subprocess
import sys
from pathlib import Path

MACHINE = sys.argv[1] if len(sys.argv) > 1 else "dev"
USER = "tvl"
DISTRO = "nixos"
MEMORY = "8G"
CPUS = "4"
DISK = "64G"
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIGS = ["configuration.nix", "home.nix"]
MAC_PATH = f"/mnt/mac{SCRIPT_DIR}"
HOME_MANAGER_URL = (
    "https://github.com/nix-community/home-manager/archive/release-25.05.tar.gz"
)
VALID_MACHINE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")


class DeployError(Exception):
    """Raised when a deploy step fails."""


def validate_machine_name(name: str) -> None:
    """Validate machine name is safe for OrbStack.

    Args:
        name: Machine name to validate.

    Raises:
        ValueError: If the name is empty or contains invalid characters.
    """
    if not name:
        raise ValueError("Machine name cannot be empty")
    if not VALID_MACHINE_RE.match(name):
        raise ValueError(
            f"Invalid machine name '{name}'. "
            "Must start with alphanumeric and contain only letters, digits, dots, dashes, underscores (max 64 chars)."
        )


def orb(*args: str) -> None:
    """Run an orb command, raising DeployError on failure.

    Args:
        *args: Arguments passed to the orb CLI.

    Raises:
        DeployError: If orb is not installed or the command fails.
    """
    try:
        subprocess.run(["orb", *args], check=True)
    except FileNotFoundError:
        raise DeployError("OrbStack CLI not found. Is OrbStack installed?")
    except subprocess.CalledProcessError as e:
        raise DeployError(f"orb {' '.join(args)} failed (exit {e.returncode})") from e


def validate_config_files() -> None:
    """Verify all required config files exist locally.

    Raises:
        FileNotFoundError: If any required config file is missing.
    """
    for config in CONFIGS:
        path = SCRIPT_DIR / config
        if not path.exists():
            raise FileNotFoundError(
                f"Required config file not found: {config}\n"
                f"Expected at: {path}"
            )


def machine_exists(name: str) -> bool:
    """Check if an OrbStack machine already exists.

    Args:
        name: Machine name to look for.

    Returns:
        True if the machine exists, False otherwise (including if orb fails).
    """
    try:
        result = subprocess.run(
            ["orb", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    if result.returncode != 0:
        return False
    return any(
        line.split()[0] == name for line in result.stdout.splitlines() if line.strip()
    )


def channel_exists(machine: str, channel_name: str) -> bool:
    """Check if a nix channel already exists in the machine.

    Args:
        machine: Machine name to check.
        channel_name: Channel name to look for.

    Returns:
        True if the channel is already registered.
    """
    try:
        result = subprocess.run(
            ["orb", "-m", machine, "sudo", "nix-channel", "--list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return any(channel_name in line for line in result.stdout.splitlines())


def create_machine(name: str) -> None:
    """Create a new NixOS OrbStack machine.

    Args:
        name: Machine name to create.

    Raises:
        DeployError: If the create command fails.
    """
    print(f"Creating NixOS machine '{name}' ({MEMORY} RAM, {CPUS} CPUs, {DISK} disk)...")
    orb(
        "create",
        "--memory", MEMORY,
        "--cpus", CPUS,
        "--disk", DISK,
        DISTRO,
        name,
    )
    print("Machine created.")


def copy_configs(machine: str) -> None:
    """Copy NixOS config files into the machine via /mnt/mac.

    Copies all config files in a single subprocess call to reduce
    orb CLI startup overhead.

    Args:
        machine: Machine name to copy configs into.

    Raises:
        DeployError: If any copy operation fails.
    """
    print("Applying configs...")
    pairs = []
    for config in CONFIGS:
        src = f"{MAC_PATH}/{config}"
        dst = f"/etc/nixos/{config}"
        print(f"  Copying {config}")
        pairs.extend([src, dst])
    orb("-m", machine, "sudo", "cp", *pairs)


def add_home_manager_channel(machine: str) -> None:
    """Add the Home Manager channel and update.

    Only adds the channel if it doesn't already exist, avoiding
    unnecessary errors on redeploys.

    Args:
        machine: Machine name to configure.

    Raises:
        DeployError: If nix-channel --update fails.
    """
    print("Adding Home Manager channel...")
    if not channel_exists(machine, "home-manager"):
        orb(
            "-m", machine, "sudo", "nix-channel", "--add",
            HOME_MANAGER_URL, "home-manager",
        )
    orb("-m", machine, "sudo", "nix-channel", "--update")


def rebuild(machine: str) -> None:
    """Run nixos-rebuild switch to apply the configuration.

    Args:
        machine: Machine name to rebuild.

    Raises:
        DeployError: If nixos-rebuild fails, with actionable hints.
    """
    print("Running nixos-rebuild switch (first run may take a while)...")
    try:
        result = subprocess.run(
            ["orb", "-m", machine, "sudo", "nixos-rebuild", "switch"],
        )
    except FileNotFoundError:
        raise DeployError("OrbStack CLI not found. Is OrbStack installed?")
    if result.returncode != 0:
        raise DeployError(
            f"nixos-rebuild switch failed (exit {result.returncode}).\n"
            "Common fixes:\n"
            "  - Verify package names at search.nixos.org\n"
            "  - Run 'orb -m dev sudo nixos-rebuild switch --show-trace' for details"
        )


def main() -> None:
    print("=== codeops-devcontainer-nixos deploy ===")
    print(f"Machine: {MACHINE}")

    try:
        validate_machine_name(MACHINE)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        validate_config_files()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        orb("status")
    except DeployError as e:
        print(f"Error: {e}")
        print("Start OrbStack first, then re-run this script.")
        sys.exit(1)

    if not machine_exists(MACHINE):
        try:
            create_machine(MACHINE)
        except DeployError as e:
            print(f"Error creating machine: {e}")
            sys.exit(1)
    else:
        print(f"Machine '{MACHINE}' already exists.")

    try:
        copy_configs(MACHINE)
        add_home_manager_channel(MACHINE)
        rebuild(MACHINE)
    except KeyboardInterrupt:
        print("\nDeploy interrupted by user.")
        sys.exit(130)
    except DeployError as e:
        print(f"\nDeploy failed: {e}")
        sys.exit(1)

    print()
    print("=== Deploy complete ===")
    print(f"Shell into the machine: orb -m {MACHINE} -u {USER}")
    print(f"Run a command:          orb -m {MACHINE} -u {USER} kubectl version --client")


if __name__ == "__main__":
    main()
