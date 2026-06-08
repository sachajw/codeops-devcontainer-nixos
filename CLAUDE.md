# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reproducible NixOS development environment running as an OrbStack Linux machine on macOS. A Python deploy script (`deploy.py`) creates and provisions the machine; two Nix config files declare all system and user state.

## Commands

```bash
python3 deploy.py              # Full deploy (create machine if needed, copy configs, rebuild)
python3 deploy.py my-machine   # Deploy to a custom machine name (default: "dev")
python3 -m pytest tests/ -v    # Run all tests
python3 -m pytest tests/test_deploy.py::TestValidateMachineName -v  # Run a single test class
```

## Architecture

**Three files, one declarative system:**

| File | Purpose |
|------|---------|
| `deploy.py` | Orchestrates machine creation, config copying, and `nixos-rebuild switch`. All OrbStack interaction goes through `orb` CLI. |
| `configuration.nix` | System-level NixOS config: packages, users, networking, Docker, Home Manager import. Imports `orbstack.nix` and `incus.nix` (not yet created). |
| `home.nix` | Home Manager config for user `tvl`: zsh (aliases, functions, vi mode), git, neovim, starship, direnv, bat, environment variables. |

**Deploy flow:** `deploy.py` validates machine name and config files → checks OrbStack is running → creates machine if missing → copies nix files into `/etc/nixos/` via `/mnt/mac/` mount → adds Home Manager channel → runs `nixos-rebuild switch`.

**Machine defaults:** 8G RAM, 4 CPUs, 64G disk. Two users: `sachawharton` (uid 502, macOS-matched) and `tvl` (uid 1000, primary dev user). Sudo is passwordless for wheel group.

**OrbStack integration:** Docker engine shared from macOS, SSH keys auto-forwarded, macOS filesystem at `/mnt/mac/`, machine filesystem at `~/OrbStack/dev/` on macOS, services accessible at `localhost`.

## Key Conventions

- **Adding packages:** Edit `environment.systemPackages` in `configuration.nix`, then `python3 deploy.py`. Verify package names at search.nixos.org.
- **Shell config:** All zsh aliases, functions, and env vars live in `home.nix` under `programs.zsh`. The escaped dollar signs (`''$\{...\}`) are Nix string interpolation escaping.
- **Nix channel:** Home Manager tracks `release-25.05`. NixOS state version is `25.11`.
- **Flakes:** Enabled (`nix-command` and `flakes` in experimental-features), but configs use channels, not flakes.
- **Tests:** `deploy.py` has full test coverage using pytest + unittest.mock. Tests mock `subprocess.run` and the `orb` helper — no OrbStack dependency needed.

## Missing Files

`configuration.nix` imports `./orbstack.nix` and `./incus.nix` which don't exist yet. The machine will fail to build until these are created or the import lines are removed.
