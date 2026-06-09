#!/usr/bin/env python3
"""Deploy codeops NixOS dev environment to an OrbStack machine."""

import sys

from config import (
    CONFIGS,
    DISTRO,
    DISK,
    HOME_MANAGER_URL,
    MAC_PATH,
    MACHINE,
    MEMORY,
    CPUS,
    USER,
    validate_config_files,
    validate_machine_name,
)
from orb import DeployError, channel_exists, machine_exists, orb, orb_run


def create_machine(name: str) -> None:
    """Create a new NixOS OrbStack machine.

    Args:
        name: Machine name to create. Must be pre-validated.

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

    Args:
        machine: Machine name to copy configs into.

    Raises:
        DeployError: If any copy operation fails.
    """
    print("Applying configs...")
    for config in CONFIGS:
        src = f"{MAC_PATH}/{config}"
        print(f"  Copying {config}")
        orb("-m", machine, "-u", "root", "cp", src, f"/etc/nixos/{config}")


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
            "-m", machine, "-u", "root", "nix-channel", "--add",
            HOME_MANAGER_URL, "home-manager",
        )
    orb("-m", machine, "-u", "root", "nix-channel", "--update")


def rebuild(machine: str) -> None:
    """Run nixos-rebuild switch to apply the configuration.

    Streams output to the terminal for immediate feedback.

    Args:
        machine: Machine name to rebuild.

    Raises:
        DeployError: If nixos-rebuild fails, with actionable hints.
    """
    print("Running nixos-rebuild switch (first run may take a while)...")
    result = orb_run("-m", machine, "-u", "root", "nixos-rebuild", "switch")
    if result.returncode != 0:
        raise DeployError(
            f"nixos-rebuild switch failed on '{machine}' (exit {result.returncode}).\n"
            "Common fixes:\n"
            "  - Verify package names at search.nixos.org\n"
            f"  - Run 'orb -m {machine} sudo nixos-rebuild switch --show-trace' for details"
        )


def main() -> None:
    print("=== codeops-devcontainer-nixos deploy ===")
    print(f"Machine: {MACHINE}")

    try:
        validate_machine_name(MACHINE)
    except (TypeError, ValueError) as e:
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

    try:
        exists = machine_exists(MACHINE)
    except DeployError as e:
        print(f"Error checking machine status: {e}")
        sys.exit(1)

    if not exists:
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
