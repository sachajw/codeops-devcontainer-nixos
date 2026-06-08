{ config, pkgs, ... }:

{
  home.stateVersion = "25.05";
  home.enableNixpkgsReleaseCheck = false;

  # --- Zsh ---
  programs.zsh = {
    enable = true;
    autosuggestion.enable = true;
    syntaxHighlighting.enable = true;
    enableCompletion = true;

    history = {
      size = 10000;
      save = 10000;
      ignoreDups = true;
      share = true;
    };

    defaultKeymap = "viins";

    shellAliases = {
      # Kubernetes
      k = "kubectl";
      kg = "kubecolor";
      kx = "kubectx";
      kns = "kubens";
      kdel = "kubectl delete";
      kgpo = "kubectl get pods";
      kd = "kubectl describe";
      kl = "kubectl logs";

      # Helm
      hlm = "helm";

      # Git
      g = "git";
      gs = "git status";
      gd = "git diff";
      gl = "git log --oneline -20";
      gp = "git push";
      gpl = "git pull";
      gc = "git commit";
      gco = "git checkout";
      gb = "git branch";
      gfa = "git fetch --all --prune";

      # Docker
      d = "docker";
      dc = "docker compose";
      dcl = "docker compose logs -f";
      dex = "docker exec -it";
      dps = "docker ps";
      drm = "docker rm";
      drmi = "docker rmi";
      dprune = "docker system prune -af";

      # Terraform
      tf = "terraform";
      tfi = "terraform init";
      tfp = "terraform plan";
      tfa = "terraform apply";

      # CLI replacements
      cat = "bat";
      ls = "eza --icons";
      ll = "eza -l --icons";
      la = "eza -la --icons";
      lt = "eza -T --icons";
      du = "dust";
      find = "fd";
      top = "btm";
      ping = "gping";

      # Navigation
      cd = "z";
      ".." = "cd ..";
      "..." = "cd ../..";

      # Misc
      t = "tmux";
      vim = "nvim";
      vi = "nvim";
    };

    initContent = ''
      # Zsh options
      setopt COMPLETE_IN_WORD
      setopt NO_BEEP
      setopt INTERACTIVE_COMMENTS
      setopt PROMPT_SUBST
      setopt NOBGNICE
      setopt HUP

      # Starship prompt
      eval "$(starship init zsh)"

      # Zoxide (z command)
      eval "$(zoxide init zsh)"

      # Direnv
      eval "$(direnv hook zsh)"

      # FZF
      eval "$(fzf --zsh)"

      # Tealdeer
      complete -C tealdeer tldr
    '';
  };

  # --- Git ---
  programs.git = {
    enable = true;
    userName = "Sacha Wharton";
    userEmail = "sacha@kubevisor.com";
    lfs.enable = true;

    delta = {
      enable = true;
      options = {
        navigate = true;
        side-by-side = true;
        line-numbers = true;
      };
    };

    extraConfig = {
      init.defaultBranch = "main";
      push.autoSetupRemote = true;
      pull.rebase = true;
      core.editor = "nvim";
      merge.conflictstyle = "diff3";
    };
  };

  # --- Neovim ---
  programs.neovim = {
    enable = true;
    defaultEditor = true;
    vimAlias = true;
    viAlias = true;
  };

  # --- Starship ---
  programs.starship = {
    enable = true;
    settings = {
      add_newline = false;
      command_timeout = 2000;
    };
  };

  # --- Direnv ---
  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
  };

  # --- Bat ---
  programs.bat = {
    enable = true;
    config.theme = "TwoDark";
  };

  # --- Environment ---
  home.sessionVariables = {
    EDITOR = "nvim";
    VISUAL = "nvim";
    KUBECONFIG = "$HOME/.kube/config";
  };
}
