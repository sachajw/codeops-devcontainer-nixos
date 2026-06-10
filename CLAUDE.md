# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reproducible NixOS development environment running as an OrbStack Linux machine on macOS. A Python deploy script creates and provisions the machine; two Nix config files declare all system and user state.

## Commands

```bash
python3 src/deploy.py              # Full deploy (create machine if needed, copy configs, rebuild)
python3 src/deploy.py my-machine   # Deploy to a custom machine name (default: "dev")
python3 -m pytest tests/ -v        # Run all tests
python3 -m pytest tests/test_deploy.py::TestValidateMachineName -v  # Run a single test class
```

## Architecture

**Deploy script split into three modules under `src/`:**

| File | Purpose |
|------|---------|
| `src/config.py` | Constants (machine name, resources, paths, Home Manager URL) and validation helpers |
| `src/orb.py` | OrbStack CLI wrapper (`orb`, `orb_run`, machine/channel existence checks) |
| `src/deploy.py` | Orchestration: create machine → copy configs → add HM channel → `nixos-rebuild switch` |

**Nix configs live in `src/` alongside deploy modules:**

| File | Purpose |
|------|---------|
| `src/configuration.nix` | System-level: packages, users, networking, Docker, Home Manager import |
| `src/home.nix` | Home Manager for user `tvl`: zsh (aliases, functions, vi mode), git, neovim, starship, direnv, bat, env vars |

**Root-level `configuration.nix` and `home.nix`** are the pre-refactor originals. `src/` versions are the active ones used by deploy.

**Deploy flow:** `deploy.py` validates machine name and config files → checks OrbStack is running → creates machine if missing → copies nix files into `/etc/nixos/` via `/mnt/mac/` mount → adds Home Manager channel → runs `nixos-rebuild switch`.

**Machine defaults:** 4G RAM, 2 CPUs, 64G disk. User `tvl` (uid 1000, primary dev user). Sudo is passwordless for wheel group.

## Key Conventions

- **Adding packages:** Edit `environment.systemPackages` in `src/configuration.nix`, then `python3 src/deploy.py`. Verify package names at search.nixos.org. Packages not in nixpkgs can be added as inline `stdenv.mkDerivation` derivations (see `azd` for an example).
- **Shell config:** All zsh aliases, functions, and env vars live in `src/home.nix` under `programs.zsh`. The escaped dollar signs (`''$\{...\}`) are Nix string interpolation escaping.
- **XDG paths:** Set in `home.sessionVariables` using `${config.xdg.configHome}` etc. to avoid ordering issues (HM sorts alphabetically).
- **Nix channel:** Home Manager tracks `release-25.05`. NixOS state version is `25.11`.
- **Flakes:** Enabled but configs use channels, not flakes.
- **Tests:** `tests/test_deploy.py` mocks `subprocess.run` and the `orb` helper — no OrbStack needed.
- **Commit format:** Emoji-prefixed conventional commits (e.g. `✨ FEATURE:`, `🐛 FIX:`, `📝 DOC:`).
- **Tools built from source:** headroom-ai is built from `/mnt/mac/.../aiops-headroom` (not PyPI) so maturin compiles the PyO3 Rust extension (`headroom._core`). Requires rustup toolchain 1.95.0 (pinned in headroom's `rust-toolchain.toml`); nixpkgs rustc 1.91.x is too old. Both are installed by home-manager activation scripts (`installRustToolchain`, `installUvTools`). Falls back to PyPI wheel if the macOS mount is absent.
- **Activation script PATH:** Home Manager activation scripts run in a minimal environment — system packages like `curl` are NOT on PATH. Use `${pkgs.curl}/bin/curl` (Nix store paths) instead of bare `curl`. Shell profile files (`~/.zshenv` etc.) are read-only Nix symlinks — use `--no-modify-path` for rustup.
