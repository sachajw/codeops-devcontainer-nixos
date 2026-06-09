{ config, pkgs, modulesPath, ... }:

let
  unstable = import (builtins.fetchTarball "channel:nixos-unstable") { config = pkgs.config; };
in
{
  imports = [
    # Container base config (filesystem, boot — required by OrbStack)
    "${modulesPath}/virtualisation/lxc-container.nix"
    # OrbStack-specific config (networking, DNS, shell integration)
    ./orbstack.nix
    # Machine-specific config (hostname)
    ./incus.nix
    # Home Manager
    <home-manager/nixos>
  ];

  # Nix settings
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  nixpkgs.config.allowUnfree = true;
  nixpkgs.config.permittedInsecurePackages = [ "docker-28.5.2" ];

  # System settings
  time.timeZone = "Europe/London";

  # Default shell
  users.defaultUserShell = pkgs.zsh;
  programs.zsh.enable = true;

  users.users.tvl = {
    uid = 1000;
    extraGroups = [ "wheel" "orbstack" "audio" "docker" ];
    isNormalUser = true;
    group = "users";
    createHome = true;
    home = "/home/tvl";
    homeMode = "700";
    useDefaultShell = true;
  };


  security.sudo.wheelNeedsPassword = false;
  users.mutableUsers = false;

  # Networking — match OrbStack defaults
  networking = {
    dhcpcd.enable = false;
    useDHCP = false;
    useHostResolvConf = false;
  };

  systemd.network = {
    enable = true;
    networks."50-eth0" = {
      matchConfig.Name = "eth0";
      networkConfig = {
        DHCP = "ipv4";
        IPv6AcceptRA = true;
      };
      linkConfig.RequiredForOnline = "routable";
    };
  };

  # Docker — OrbStack provides the engine and CLI natively, no need for NixOS Docker

  # System packages
  environment.systemPackages = with pkgs; [
    # --- Kubernetes ---
    kubectl
    kubecolor
    kubernetes-helm
    stern
    krew
    helm-docs
    chart-testing
    kompose
    polaris
    kor
    kubeshark
    kubelogin
    argocd
    fluxcd
    k3sup
    k0sctl

    # --- Infrastructure / IaC ---
    terraform
    terragrunt
    terramate
    terraform-docs
    tflint
    infracost
    ansible

    (stdenv.mkDerivation rec {
      pname = "azd";
      version = "1.25.5";
      src = fetchurl {
        url = "https://github.com/Azure/azure-dev/releases/download/azure-dev-cli_${version}/azd-linux-amd64.tar.gz";
        hash = "sha256-h45MPTkA/qTmXV56A3GCjKEnoKx9G1jALEpa81ZNHEk=";
      };
      sourceRoot = ".";
      installPhase = "install -Dm755 azd-linux-amd64 $out/bin/azd";
    })
    hcledit
    inframap

    # Wiz CLI
    (stdenv.mkDerivation rec {
      pname = "wizcli";
      version = "1.50.0";
      src = fetchurl {
        url = "https://downloads.wiz.io/v1/wizcli/${version}/wizcli-linux-arm64";
        hash = "sha256-qedvItVFvMft/jjosdlIp5hW1MvW3rmfmDjuM3mmdMo=";
      };
      unpackPhase = "true";
      installPhase = "install -Dm755 $src $out/bin/wizcli";
    })

    # --- Containers ---
    docker
    docker-compose
    crane
    skopeo
    dive
    lazydocker
    oras
    syft
    trivy

    # --- Languages ---
    nodejs
    python3
    go
    bun

    # --- Git ---
    git
    git-lfs
    delta
    git-filter-repo
    ripsecrets
    gh

    # --- CLI essentials ---
    jq
    unstable.acli
    yq-go
    curl
    wget
    neovim
    tmux
    fzf
    ripgrep
    bat
    eza
    fd
    starship
    zoxide
    tealdeer
    procs
    dust
    duf
    bottom
    halp
    htop
    hyperfine
    tokei
    lsd
    lnav
    entr
    pv
    parallel
    atuin
    hexyl
    htmlq
    watch
    multitail
    lynx
    diff-so-fancy
    usql

    # --- Security ---
    sops
    age
    gnupg
    pass
    mkcert
    trufflehog
    gitleaks
    scorecard

    # --- Network ---
    nmap
    socat
    websocat
    mosh
    bandwhich
    gping

    # --- Dev tools ---
    pre-commit
    uv
    poetry
    ruff
    yamllint
    sqlfluff
    jsonnet
    commitizen
    shellcheck
    shfmt
    pipx
    pylint
    d2
    graphviz
    pandoc
    asciinema

    # --- Cloud ---
    rclone

    # --- Shell extras ---
    direnv
    nix-direnv
    zsh-autosuggestions
    zsh-syntax-highlighting
    zsh-completions

    # --- Fun ---
    sl
    cmatrix
    fortune
    toilet
    cowsay
    asciiquarium

    # --- Extra tools (referenced by aliases/functions) ---
    kubectx
    xcp
    safe-rm
    mob
    git-quick-stats
    p7zip
    unrar
    ffmpeg
    asciinema
  ];

  # Home Manager
  home-manager.users.tvl = import ./home.nix;

  system.stateVersion = "25.11";
}
