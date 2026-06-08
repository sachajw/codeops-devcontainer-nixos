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
# Shell into the machine
orb -m dev

# Run a single command
orb -m dev kubectl get pods
orb -m dev terraform plan

# Open a specific shell
orb -m dev zsh
```

## Adding Packages

Edit `configuration.nix` and add your package to `environment.systemPackages`, then re-deploy:

```bash
python3 deploy.py
```

## Updating

Update all packages by rebuilding:

```bash
orb -m dev sudo nix-channel --update
python3 deploy.py
```

## Rollback

NixOS keeps previous generations. To rollback:

```bash
orb -m dev sudo nixos-rebuild switch --rollback
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
configuration.nix   System packages, Docker, zsh, Home Manager
home.nix            Shell aliases, git config, nvim, starship
deploy.py           One-command deploy script
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
