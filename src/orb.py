"""OrbStack CLI wrapper and machine queries."""

import subprocess


class DeployError(Exception):
    """Raised when a deploy step fails."""


def orb(*args: str) -> None:
    """Run an orb command, raising DeployError on failure.

    Raises:
        DeployError: If orb is not installed or the command fails.
    """
    try:
        subprocess.run(
            ["orb", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise DeployError("OrbStack CLI not found. Is OrbStack installed?")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        parts = [f"orb {' '.join(args)} failed (exit {e.returncode})"]
        if stderr:
            parts.append(stderr)
        raise DeployError("\n".join(parts)) from e


def orb_run(*args: str) -> subprocess.CompletedProcess:
    """Run an orb command and return the result without raising on non-zero exit.

    Streams stdout/stderr to the terminal for long-running commands,
    avoiding buffering large outputs in memory.

    Raises:
        DeployError: If orb is not installed or the command cannot be launched.
    """
    try:
        return subprocess.run(
            ["orb", *args],
            check=False,
            capture_output=False,
            text=True,
        )
    except FileNotFoundError:
        raise DeployError("OrbStack CLI not found. Is OrbStack installed?")
    except OSError as e:
        raise DeployError(f"orb {' '.join(args)} failed: {e}") from e


def machine_exists(name: str) -> bool:
    """Check if an OrbStack machine already exists.

    Args:
        name: Machine name to look for.

    Returns:
        True if the machine exists, False otherwise.

    Raises:
        DeployError: If orb is not installed or fails unexpectedly.
    """
    try:
        result = subprocess.run(
            ["orb", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise DeployError("OrbStack CLI not found. Is OrbStack installed?")
    except OSError as e:
        raise DeployError(f"Failed to run 'orb list': {e}") from e

    if result.returncode != 0:
        return False
    return any(
        fields[0] == name
        for line in result.stdout.splitlines()
        if line.strip() and (fields := line.split())
    )


def channel_exists(machine: str, channel_name: str) -> bool:
    """Check if a nix channel already exists in the machine.

    Args:
        machine: Machine name to check.
        channel_name: Channel name to look for.

    Returns:
        True if the channel is registered, False otherwise.

    Raises:
        DeployError: If the channel list query fails unexpectedly.
    """
    try:
        result = subprocess.run(
            ["orb", "-m", machine, "-u", "root", "nix-channel", "--list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise DeployError("OrbStack CLI not found. Is OrbStack installed?")
    except OSError as e:
        raise DeployError(f"Failed to query channels on '{machine}': {e}") from e

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else ""
        raise DeployError(
            f"Failed to list nix channels on '{machine}' (exit {result.returncode})"
            + (f": {stderr}" if stderr else "")
        )
    return any(channel_name in line for line in result.stdout.splitlines())
