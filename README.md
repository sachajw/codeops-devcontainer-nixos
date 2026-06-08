# codeops-devcontainer-nixos

Reproducible NixOS development environment running as an OrbStack Linux machine. Declarative config, version-controlled, deployable on any Mac with OrbStack.

## Prerequisites

- macOS with [OrbStack](https://orbstack.dev/) installed
- That's it. NixOS handles the rest.

## Quick Start

```bash
git clone git@github.com:sachajw/codeops-devcontainer-nixos.git
cd codeops-devcontainer-nixos
python3 deploy.py
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
| RAM | 8 GB |
| CPUs | 4 |
| Disk | 64 GB |
| Shell | zsh + starship |

## What's Included

### System Packages (100+)

| Category | Packages |
|----------|----------|
| **Kubernetes** | kubectl, kubecolor, helm, stern, krew, argocd, fluxcd, kubectx, kubelogin, kompose, polaris, kor, kubeshark, chart-testing |
| **IaC** | terraform, terragrunt, terramate, tflint, infracost, ansible, azure-cli, awscli2 |
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
- XDG paths for AWS, Azure, Docker, GPG, Krew
- kubectl shorthands: `$do` (dry-run yaml), `$now` (force delete), `$dry`

## Adding Packages

Edit `configuration.nix` and add your package to `environment.systemPackages`, then re-deploy:

```bash
python3 deploy.py
```

Verify package names at [search.nixos.org](https://search.nixos.org).

## Modifying Shell Config

All aliases, functions, and env vars live in `home.nix` under `programs.zsh`. Edit and redeploy:

```bash
python3 deploy.py
```

Note: The `''$\{...\}` syntax in `initContent` is Nix string interpolation escaping — double single quotes and escaped dollar signs.

## Testing

```bash
python3 -m pytest tests/ -v                            # Run all 47 tests
python3 -m pytest tests/test_deploy.py::TestMain -v    # Run a single test class
```

Tests mock `subprocess.run` and the `orb` CLI — no OrbStack dependency needed. Coverage is 99%.

## Updating

Update all packages by rebuilding:

```bash
orb -m dev -u tvl sudo nix-channel --update
python3 deploy.py
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

## File Structure

```
configuration.nix   System packages, user, Docker, networking, Home Manager
home.nix            Shell aliases (150+), functions (15+), git, nvim, starship, env vars
deploy.py           One-command deploy script (47 tests, 99% coverage)
tests/              Full test coverage for deploy.py
```

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

## Known Issues

- `configuration.nix` imports `./orbstack.nix` and `./incus.nix` which don't exist yet — these are placeholders for future config
- Home Manager channel tracks `release-25.05`; NixOS state version is `25.11`
