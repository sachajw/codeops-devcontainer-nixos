# codeops-devcontainer-nixos

Reproducible NixOS development environment running as an OrbStack Linux machine. Declarative config, version-controlled, deployable on any Mac with OrbStack.

## Prerequisites

- macOS with [OrbStack](https://orbstack.dev/) installed
- That's it. NixOS handles the rest.

## Quick Start

```bash
git clone git@github.com:sachajw/codeops-devcontainer-nixos.git
cd codeops-devcontainer-nixos
python3 src/deploy.py
```

This creates a NixOS machine named `dev` in OrbStack and applies the configuration.

## Usage

```bash
# Shell into the machine (from any terminal — OrbStack, Warp, iTerm, etc.)
orb -m dev -u tvl

# Run a single command
orb -m dev -u tvl kubectl get pods
orb -m dev -u tvl terraform plan
```

## Machine Specs

| Setting | Value |
|---------|-------|
| Machine name | `dev` |
| User | `tvl` (uid 1000) |
| OS | NixOS 25.11 |
| RAM | 4 GB |
| CPUs | 2 |
| Disk | 64 GB |
| Shell | zsh + starship |

## What's Included

### System Packages (100+)

| Category | Packages |
|----------|----------|
| **Kubernetes** | kubectl, kubecolor, helm, stern, krew, argocd, fluxcd, kubectx, kubelogin, kompose, polaris, kor, kubeshark, chart-testing |
| **IaC** | terraform, terragrunt, terramate, tflint, infracost, ansible, azure-cli, azd (custom derivation), awscli2 |
| **Containers** | docker, docker-compose, crane, skopeo, dive, lazydocker, trivy, syft |
| **Languages** | nodejs, python3, go, bun |
| **Git** | git, git-lfs, delta, gh, git-filter-repo, ripsecrets |
| **CLI** | jq, yq, neovim, tmux, fzf, ripgrep, bat, eza, fd, starship, zoxide, tealdeer, bottom, dust, hyperfine, lnav |
| **Security** | sops, age, gnupg, pass, mkcert, trufflehog, gitleaks |
| **Network** | nmap, socat, mosh, gping, bandwhich |
| **Dev tools** | pre-commit, uv, ruff, shellcheck, pandoc, asciinema, d2 |

### Shell Aliases (150+)

| Category | Examples |
|----------|----------|
| **Kubernetes** | `k` (kubecolor), `kaf`, `kdf`, `kgpo`, `kdelns`, `kgnodes`, `kgsec`, `kl`, `kx` (kubectx), `kns` (kubens) |
| **Helm** | `hlm`, `hlminstall`, `hlmrepoadd`, `hlmtemp`, `hlmupgrade` |
| **Git** | `g`, `gs`, `gd`, `glog`, `gstash`, `gres`, `gwt`, `gcob`, `gap` |
| **Terraform** | `tf`, `tfi`, `tfp`, `tfa`, `tfaauto`, `tfd` |
| **Docker** | `d`, `dc`, `dcl`, `dex`, `dps`, `dprune` |
| **CLI replacements** | `cat`→bat, `ls`→eza, `du`→dust, `find`→fd, `top`→btm, `rm`→safe-rm, `cp`→xcp, `ping`→gping |

### Shell Functions (15+)

| Function | Description |
|----------|-------------|
| `mkcd` | Create dir and cd into it |
| `extract` | Extract any archive format |
| `killproc` | Find and kill processes by name |
| `weather` | Weather via wttr.in |
| `backup` | Timestamped file backup |
| `ff` / `find-dir` | Find files/dirs by name |
| `filesize` | Human-readable file size |
| `serve` | Quick HTTP server (python3) |
| `docker-cleanup` | Prune containers, images, volumes, networks |
| `git-cleanup` | Delete merged branches |
| `note` | Quick timestamped notes in `~/Notes/` |
| `azten` | Azure subscription switcher (fzf) |
| `aksfresh` | Refresh kubelogin tokens for AAD contexts |
| `pcc` | Compose pre-commit configs from templates |

### Environment Variables

- `EDITOR` / `VISUAL` = nvim
- `KUBECONFIG` = `~/.kube/config`
- `KUBE_EDITOR` = nvim
- XDG paths for AWS, Azure, azd, Docker, GPG, Krew
- kubectl shorthands: `$do` (dry-run yaml), `$now` (force delete), `$dry`

## File Structure

```
src/
  config.py            Constants, machine name validation
  orb.py               OrbStack CLI wrapper
  deploy.py            Deploy orchestration (create, copy, rebuild)
  configuration.nix    System packages, users, networking, Home Manager
  home.nix             Shell config, git, nvim, starship, env vars
tests/
  test_deploy.py       Full test coverage for deploy pipeline
docs/
  gui-desktop.md       GUI/desktop setup notes
```

Root-level `configuration.nix` and `home.nix` are pre-refactor originals; `src/` versions are the active ones.

## Adding Packages

Edit `src/configuration.nix` and add your package to `environment.systemPackages`, then re-deploy:

```bash
python3 src/deploy.py
```

Verify package names at [search.nixos.org](https://search.nixos.org). For packages not in nixpkgs, add an inline `stdenv.mkDerivation` derivation (see `azd` in `src/configuration.nix` for an example).

## Modifying Shell Config

All aliases, functions, and env vars live in `src/home.nix` under `programs.zsh`. Edit and redeploy:

```bash
python3 src/deploy.py
```

Note: The `''$\{...\}` syntax in `initContent` is Nix string interpolation escaping — double single quotes and escaped dollar signs.

## Testing

```bash
python3 -m pytest tests/ -v                            # Run all tests
python3 -m pytest tests/test_deploy.py::TestMain -v    # Run a single test class
```

Tests mock `subprocess.run` and the `orb` CLI — no OrbStack dependency needed. Coverage is 99%.

## Updating

Update all packages by rebuilding:

```bash
orb -m dev -u tvl sudo nix-channel --update
python3 src/deploy.py
```

## Rollback

NixOS keeps previous generations. To rollback:

```bash
orb -m dev -u tvl sudo nixos-rebuild switch --rollback
```

## Backup

Export the machine to a file:

```bash
orb export dev dev-backup.tar.zst
```

Import on another Mac:

```bash
orb import -n dev dev-backup.tar.zst
```

## NixOS

The machine runs NixOS 25.11 on channels (not flakes). Home Manager tracks `release-25.05`.

### Config Layout

| File | Scope |
|------|-------|
| `src/configuration.nix` | System packages, users, networking, Docker, Home Manager import |
| `src/home.nix` | User `tvl`: zsh, git, nvim, starship, direnv, bat, aliases, functions, env vars |

Changes to either file require a deploy (`python3 src/deploy.py`) to take effect. NixOS is declarative — manual changes inside the machine are lost on rebuild.

### Useful Commands (inside the machine)

```bash
# Package management
nix-env -qaP <pkg>                # Search for a package
nix-env -qaP --installed <pkg>    # Check if a package is installed
nix-store --query --references /run/current-system/sw  # List all system packages

# System maintenance
nix-collect-garbage -d            # Remove old generations and free disk
nix-store --optimise              # Hard-link identical files to save space
nixos-rebuild switch --rollback   # Roll back to previous generation

# Inspect config
nixos-option services.docker.enable   # Check a NixOS option value
nixos-version                         # Show current NixOS version

# Home Manager (run as tvl, not root)
home-manager generations           # List all HM generations
home-manager rollback              # Roll back user config
```

### Channels

```bash
# List channels
nix-channel --list

# Update all channels (pulls latest package versions)
sudo nix-channel --update

# Then redeploy to apply
exit  # back to macOS
python3 src/deploy.py
```

### macOS Mount

OrbStack exposes the macOS filesystem at `/mnt/mac/`. The deploy script copies configs through this mount. Your macOS home is at:

```
/mnt/mac/Users/sachawharton/
```

The `home.nix` activation script symlinks `.agents` and `.ccs` from macOS into the NixOS home for cross-machine tool access.

### Tools Built from Source

Some tools are built from local source repos (accessible via `/mnt/mac/`) during the first deploy activation:

| Tool | Source | Why |
|------|--------|-----|
| **headroom-ai** | `~/Documents/repos/aiops/aiops-headroom` | PyPI wheel ships Python-only; building from source compiles the PyO3 Rust extension (`headroom._core`) for full proxy functionality |
| **rustup** (1.95.0) | `https://sh.rustup.rs` | headroom pins rustc 1.95.0 in `rust-toolchain.toml`; nixpkgs ships 1.91.x which is too old |

The Rust toolchain is installed to `~/.local/share/rustup/` with `--no-modify-path` (PATH is managed by `home.sessionVariables`). If the macOS source repo mount is unavailable, headroom falls back to the PyPI wheel (Python-only, no Rust extension).

To rebuild headroom after source changes:
```bash
orb -m dev -u tvl
uv tool install --force "/mnt/mac/Users/sachawharton/Documents/repos/aiops/aiops-headroom[all]"
```

Headroom proxy runs as a systemd user service (auto-starts on login). Dashboard: **http://localhost:8787/dashboard**

### Azure Login

`az` is installed but requires authentication per-machine. The `azten` function handles this automatically — if not logged in, it triggers device-code login before showing the fzf subscription picker. To log in manually:

```bash
az login --use-device-code
```

### Troubleshooting

| Problem | Fix |
|---------|-----|
| Package not found | Verify name at [search.nixos.org](https://search.nixos.org), check channel is up to date (`sudo nix-channel --update`) |
| Build fails after adding a package | Run `orb -m dev sudo nixos-rebuild switch --show-trace` for the full error |
| Disk full | `nix-collect-garbage -d` removes old generations |
| Config change not applying | Make sure you edited `src/` files, not root-level ones — then redeploy |
| `az account list` is empty | Run `az login --use-device-code` (or just run `azten`) |
| `headroom._core` import fails | Rebuild from source: `uv tool install --force "/mnt/mac/.../aiops-headroom[all]"` (requires rustup 1.95.0) |

## OrbStack Integration

| Feature | Details |
|---------|---------|
| Docker | OrbStack engine shared — `docker` works inside machine |
| SSH keys | Auto-forwarded from macOS |
| macOS files | Accessible at `/mnt/mac/` |
| Machine files | Accessible at `~/OrbStack/dev/` from macOS |
| Network | Services at `localhost` from macOS |
| VPN | Follows macOS VPN/DNS automatically |
| SSL certs | Uses macOS keychain |
