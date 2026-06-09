{ config, pkgs, lib, ... }:

{
  home.stateVersion = "25.05";
  home.enableNixpkgsReleaseCheck = false;

  # XDG base directories — must be set before sessionVariables that reference them
  xdg.enable = true;

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
      path = "${config.xdg.stateHome}/zsh/history";
    };

    defaultKeymap = "viins";

    initContent = ''
      # Zsh options
      setopt COMPLETE_IN_WORD
      setopt NO_BEEP
      setopt INTERACTIVE_COMMENTS
      setopt PROMPT_SUBST
      setopt NOBGNICE
      setopt HUP
      setopt INC_APPEND_HISTORY

      # kubectl shorthand exports
      export do="--dry-run=client -oyaml"
      export now="--force --grace-period 0"
      export dry="--dry-run=client -o yaml"

      # Starship prompt
      eval "$(starship init zsh)"

      # Zoxide (z command)
      eval "$(zoxide init zsh)"

      # Direnv
      eval "$(direnv hook zsh)"

      # FZF
      eval "$(fzf --zsh)"

      # Tealdeer
      compdef _gnu_generic tldr

      # --- Shell functions ---

      mkcd() { mkdir -p "$1" && cd "$1"; }

      extract() {
        if [[ -f $1 ]]; then
          case $1 in
            *.tar.bz2)   tar xjf "$1"     ;;
            *.tar.gz)    tar xzf "$1"     ;;
            *.bz2)       bunzip2 "$1"     ;;
            *.rar)       unrar e "$1"     ;;
            *.gz)        gunzip "$1"      ;;
            *.tar)       tar xf "$1"      ;;
            *.tbz2)      tar xjf "$1"     ;;
            *.tgz)       tar xzf "$1"     ;;
            *.zip)       unzip "$1"       ;;
            *.Z)         uncompress "$1"  ;;
            *.7z)        7z x "$1"        ;;
            *)           echo "'$1' cannot be extracted via extract()" ;;
          esac
        else
          echo "'$1' is not a valid file"
        fi
      }

      killproc() {
        local proc_name="$1"
        if [[ -z "$proc_name" ]]; then
          echo "Usage: killproc <process_name>"
          return 1
        fi
        local pids=$(pgrep -f "$proc_name")
        if [[ -n "$pids" ]]; then
          echo "Found processes:"
          ps -p $pids
          echo -n "Kill these processes? (y/N) "
          read -r response
          if [[ "$response" == "y" || "$response" == "Y" ]]; then
            kill $pids
            echo "Processes killed."
          fi
        else
          echo "No processes found matching '$proc_name'"
        fi
      }

      weather() { curl -s "wttr.''$\{1:-\}" ; }

      backup() {
        local file="$1"
        if [[ -f "$file" ]]; then
          cp "$file" "''$\{file\}.backup.$(date +%Y%m%d_%H%M%S)"
          echo "Backup created: ''$\{file\}.backup.$(date +%Y%m%d_%H%M%S)"
        else
          echo "File '$file' does not exist"
        fi
      }

      ff() { find . -type f -name "*$1*"; }
      find-dir() { find . -type d -name "*$1*"; }

      filesize() {
        if [[ -f "$1" ]]; then
          stat -c%s "$1" 2>/dev/null | numfmt --to=iec || ls -lh "$1" | awk '{print $5}'
        else
          echo "File '$1' does not exist"
        fi
      }

      serve() {
        local port="''$\{1:-8000\}"
        echo "Starting HTTP server on port $port..."
        echo "Access at: http://localhost:$port"
        python3 -m http.server "$port"
      }

      docker-cleanup() {
        echo "Removing stopped containers..."
        docker container prune -f
        echo "Removing unused images..."
        docker image prune -f
        echo "Removing unused volumes..."
        docker volume prune -f
        echo "Removing unused networks..."
        docker network prune -f
        echo "Docker cleanup complete!"
      }

      git-cleanup() {
        echo "Fetching latest changes..."
        git fetch --prune
        echo "Merged branches (excluding main/master):"
        git branch --merged | grep -v '\*\|main\|master' | xargs -n 1 git branch -d
        echo "Git cleanup complete!"
      }

      note() {
        local note_dir="$HOME/Notes"
        local note_file="$note_dir/$(date +%Y-%m-%d).md"
        mkdir -p "$note_dir"
        if [[ $# -eq 0 ]]; then
          ''$\{EDITOR:-nvim\} "$note_file"
        else
          echo "$(date '+%H:%M') - $*" >> "$note_file"
          echo "Note added to $note_file"
        fi
      }

      # Azure subscription switcher (fzf)
      azten() {
        if ! command -v az >/dev/null 2>&1; then
          echo "az not found"; return 1
        fi
        if ! command -v fzf >/dev/null 2>&1; then
          echo "fzf not found"; return 1
        fi
        local sub_line sub_id sub_name
        sub_line=$(az account list --query '[].{Name:name, Id:id}' -o tsv \
          | awk -F'\t' '{printf "%-40s %s\n", $1, $2}' \
          | fzf --prompt='Subscription> ') || return 1
        sub_name=$(echo "$sub_line" | awk '{$NF=""; print $0}' | sed 's/[[:space:]]*$//')
        sub_id=$(echo "$sub_line" | grep -o '[0-9a-f-]\{36\}')
        az account set --subscription "$sub_id"
        echo "  Subscription: $sub_name"
      }

      # Refresh kubelogin tokens for AAD-enabled contexts
      aksfresh() {
        if ! command -v kubelogin >/dev/null 2>&1; then
          echo "kubelogin not found"; return 1
        fi
        local current
        current=$(kubectl config current-context 2>/dev/null)
        kubelogin get-token --login azurecli --server-id 6dae42f8-4368-4678-94ff-3960e28e3630 2>/dev/null
        echo "Token refreshed for current context: ''$\{current:-none\}"
      }

      # pre-commit config composer
      pcc() {
        local dir=".pre-commit-config.d"
        mkdir -p "$dir"
        for tmpl in "$@"; do
          local src="$HOME/.config/pre-commit/templates/''$\{tmpl\}.yaml"
          if [ -f "$src" ]; then
            ln -sf "$src" "$dir/''$\{tmpl\}.yaml"
            echo "Added: $tmpl"
          else
            echo "Not found: $tmpl"
            return 1
          fi
        done
        echo "Configs in $dir:"
        ls -1 "$dir/"
      }
    '';

    shellAliases = {
      # --- Zsh management ---
      szsh = "source ~/.zshrc";
      ezsh = "nvim ~/.zshrc";

      # --- Shell ---
      c = "clear";
      nowdt = "date +'%T'";
      nowt = "nowdt";
      nowd = "date +'%m-%d-%Y'";
      df = "df -hPT | column -t";
      t = "tmux";
      vim = "nvim";
      vi = "nvim";
      ct = "column -t";
      sha = "shasum -a 256";
      hs = "history";
      hsg = "history grep -i";
      j = "jobs -l";

      # --- Navigate ---
      mkdir = "mkdir -pv";
      ".." = "cd ..";
      "..." = "cd ../../../";
      "...." = "cd ../../../../";

      # --- Compression ---
      untar = "tar -xvzf";
      listtar = "tar -tzf";
      dirtar = "tar -xvzf -C";
      createtar = "tar -cvzf";
      extracttar = "tar -xvf";

      # --- Copy ---
      cp = "xcp";

      # --- Diff ---
      dsf = "diff-so-fancy";

      # --- Find ---
      findfile = "find . -type f -name";

      # --- Grep ---
      grep = "grep --color=auto";
      egrep = "egrep --color=auto";
      fgrep = "fgrep --color=auto";

      # --- File manipulation ---
      cpover = "\\cp";
      mvover = "\\mv";
      lnover = "\\ln";
      ln = "ln -i";

      # --- CLI replacements ---
      cat = "bat --paging=auto";
      ls = "eza --icons";
      ll = "eza -alF --icons";
      la = "eza -A --icons";
      lt = "eza -T --icons";
      l = "eza -d .* --color=auto";
      tree = "eza --tree";
      du = "dust";
      find = "fd";
      top = "btm";
      ping = "gping -c 5";
      rm = "safe-rm";

      # --- Kubernetes ---
      k = "kubecolor";
      kubectl = "kubecolor";
      kx = "kubectx";
      kns = "kubens";
      kdel = "kubectl delete";
      kd = "kubectl describe";
      kl = "kubectl logs";
      kgpo = "kubectl get pods";
      kgpodall = "kubectl get pods --all-namespaces -owide";
      kgpodwide = "kubectl get pods -o wide";
      kgall = "kubectl get all";
      kapi = "kubectl api-resources -o wide --sort-by name";
      kaf = "kubectl apply -f";
      kak = "kubectl apply -k";
      kdf = "kubectl delete -f";
      kci = "kubectl cluster-info";
      kconset = "kubectl config set-context --current --namespace";
      kcp = "kubectl cp";
      kgcm = "kubectl get configmap";
      keditcm = "kubectl edit configmap";
      kdelcm = "kubectl delete configmap";
      kgcrd = "kubectl get crd";
      kdelcrd = "kubectl delete crd";
      keditcrd = "kubectl edit crd";
      kdelallpod = "kubectl delete pods --all=true";
      kdelpod = "kubectl delete pods";
      kgdep = "kubectl get deployment";
      keditdep = "kubectl edit deployment";
      kdeldep = "kubectl delete deployment";
      kdesdep = "kubectl describe deployment";
      krollstatusdep = "kubectl rollout status deploy -w";
      krollrestartdep = "kubectl rollout restart deploy";
      kdespod = "kubectl describe pods";
      kgpod = "kubectl get pods";
      kgnodes = "kubectl get nodes -owide";
      kdesnodes = "kubectl describe nodes";
      klogs = "kubectl logs";
      klogsf = "kubectl logs -f";
      kgns = "kubectl get ns";
      kdelns = "kubectl delete ns";
      ktopn = "kubectl top nodes";
      ktopp = "kubectl top pods";
      kgpv = "kubectl get pv";
      kgpvc = "kubectl get pvc";
      kgsec = "kubectl get secrets";
      kdessec = "kubectl describe secrets";
      kdelsec = "kubectl delete secrets";
      kgsa = "kubectl get sa";
      kgsvc = "kubectl get svc";
      kdessvc = "kubectl describe svc";
      kdelsvc = "kubectl delete svc";
      kging = "kubectl get ingress";
      kgevents = "kubectl get events --sort-by='.metadata.creationTimestamp'";
      krun = "kubectl run";
      kscaledep = "kubectl scale deployment";
      kdelallpodsns = "kubectl delete pods --all-namespaces=true";
      kver = "kubectl version --client";
      krewin = "kubectl krew install";

      # --- Helm ---
      hlm = "helm";
      hlminstall = "helm install";
      hlmrepoadd = "helm repo add";
      hlmrepoupdate = "helm repo update";
      hlmsearch = "helm search";
      hlmlist = "helm list";
      hlmuninstall = "helm uninstall";
      hlmpull = "helm pull";
      hlmupgrade = "helm upgrade";
      hlmrollback = "helm rollback";
      hlmhist = "helm history";
      hlmlint = "helm lint";
      hlmtemp = "helm template";

      # --- Terraform / IaC ---
      tf = "terraform";
      tfi = "terraform init";
      tfp = "terraform plan";
      tfa = "terraform apply";
      tfaauto = "terraform apply -auto-approve";
      tfd = "terraform destroy";
      tm = "terramate";

      # --- Git ---
      g = "git";
      gs = "git status";
      gd = "git diff";
      gdf = "git diff";
      gl = "git log --oneline -20";
      gp = "git push";
      gph = "git push";
      gpl = "git pull";
      gc = "git clone";
      gcom = "git commit";
      gcomm = "git commit -m";
      gco = "git checkout";
      gcob = "git checkout -b";
      gb = "git branch -a";
      gbd = "git branch -d";
      gfa = "git fetch --all --prune";
      gstash = "git stash";
      gstashpop = "git stash pop";
      gres = "git reset --soft HEAD~1";
      glog = "git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit";
      glog1 = "git log --oneline";
      gshow = "git show";
      gblame = "git blame";
      gclean = "git clean -fd";
      grevert = "git revert";
      grestore = "git restore .";
      gwt = "git worktree";
      gwtl = "git worktree list";
      gwta = "git worktree add";
      gwtr = "git worktree remove";
      gcg = "git config --edit --global";
      gcl = "git config --edit --local";
      gap = "git ai-push";

      # --- Docker ---
      d = "docker";
      dc = "docker compose";
      dcl = "docker compose logs -f";
      dex = "docker exec -it";
      dps = "docker ps";
      drm = "docker rm";
      drmi = "docker rmi";
      dprune = "docker system prune -af";

      # --- Kustomize ---
      kzb = "kustomize build";

      # --- Netops ---
      header = "curl -I";
      headerc = "curl -I --compress";
      pub = "curl ipinfo.io/ip";

      # --- Pre-commit ---
      pcinstall = "pre-commit install";
      pcall = "pre-commit run --all-files";
      pcup = "pre-commit autoupdate";

      # --- Mob ---
      ms = "mob start";
      mn = "mob next";
      md = "mob done";
      moo = "mob moo";

      # --- Permissions ---
      chown = "chown --preserve-root";
      chmod = "chmod --preserve-root";
      chgrp = "chgrp --preserve-root";

      # --- Sudo ---
      root = "sudo -i";

      # --- Misc ---
      arec = "asciinema rec";
    };
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

  # --- macOS symlinks (via OrbStack /mnt/mac mount) ---
  home.activation.linkMacDirs = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    if [ ! -L "$HOME/.agents" ]; then
      rm -rf "$HOME/.agents" 2>/dev/null || true
      ln -s /mnt/mac/Users/sachawharton/.agents "$HOME/.agents"
    fi
    if [ ! -L "$HOME/.ccs" ]; then
      rm -rf "$HOME/.ccs" 2>/dev/null || true
      ln -s /mnt/mac/Users/sachawharton/.ccs "$HOME/.ccs"
    fi
  '';

  # --- Environment ---
  home.sessionVariables = {
    EDITOR = "nvim";
    VISUAL = "nvim";
    KUBECONFIG = "$HOME/.kube/config";
    KUBE_EDITOR = "nvim";
    KUBECONFIG_CONTEXT_DEADLINE = "300";

    # XDG-derived paths — use Nix interpolation to avoid ordering issues
    # (HM sorts sessionVariables alphabetically, so $XDG_* refs resolve
    # before XDG_* exports in hm-session-vars.sh)
    AWS_SHARED_CREDENTIALS_FILE = "${config.xdg.configHome}/aws/credentials";
    AWS_CONFIG_FILE = "${config.xdg.configHome}/aws/config";
    AZURE_CONFIG_DIR = "${config.xdg.dataHome}/azure";
    AZD_CONFIG_DIR = "${config.xdg.configHome}/azd";
    DOCKER_CONFIG = "${config.xdg.configHome}/docker";
    GNUPGHOME = "${config.xdg.dataHome}/gnupg";
    KREW_ROOT = "${config.xdg.dataHome}/krew";

    # macOS mount paths
    AGENTS_HOME = "$HOME/.agents";
    CCS_HOME = "$HOME/.ccs";
    CCS_MAC_HOME = "/mnt/mac/Users/sachawharton/.ccs";

    # PATH additions
    PATH = "$HOME/.local/bin:$HOME/.local/share/cargo/bin:$HOME/go/bin:${config.xdg.dataHome}/krew/bin:$PATH";
  };
}
