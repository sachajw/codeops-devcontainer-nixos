# GUI / Desktop Options

OrbStack Linux machines are **headless by default** — no built-in display forwarding, X11, Wayland, or VNC passthrough. However, you can add a GUI using one of the approaches below.

---

## Option A: VNC + XFCE (Full Desktop)

The most practical option for a full desktop experience. Adds a lightweight XFCE desktop and TigerVNC server, accessible from macOS Screen Sharing or any VNC client.

### NixOS Config

Add to `configuration.nix`:

```nix
# Enable X11 and XFCE
services.xserver = {
  enable = true;
  desktopManager.xfce.enable = true;
  displayManager.lightdm.enable = false;  # VNC handles login
};

# TigerVNC server
services.tigervnc = {
  server = {
    enable = true;
    # Create a VNC password: orb -m dev -u tvl vncpasswd
    # Then set the password file path here
    passwordFile = "/home/tvl/.vnc/passwd";
    openFirewall = true;  # Opens port 5901
    extraArguments = [ "-localhost" "-geometry" "1920x1080" "-depth" "24" ];
  };
};

# Required packages
environment.systemPackages = with pkgs; [
  tigervnc           # vncpasswd utility
  xorg.xorgserver    # X server
  xfce.xfce4-terminal
];
```

### Setup

1. **Set VNC password:**
   ```bash
   orb -m dev -u tvl vncpasswd
   ```

2. **Rebuild:**
   ```bash
   python3 deploy.py
   ```

3. **Connect from macOS:**
   - Open **Screen Sharing** (or RealVNC Viewer)
   - Connect to `localhost:5901`
   - Enter the VNC password

### Resource Impact
- ~1-2 GB extra disk space
- ~200-400 MB extra RAM when running
- Recommendation: increase VM memory to 8G in `deploy.py` if using a desktop

---

## Option B: X11 Forwarding (Individual Apps)

Lightest option — forwards individual GUI application windows to macOS over SSH. No full desktop, just app windows rendered on your Mac.

### NixOS Config

Add to `configuration.nix` `environment.systemPackages`:

```nix
environment.systemPackages = with pkgs; [
  xorg.xorgserver
  xorg.xauth
  # Add any GUI apps you want to forward, e.g.:
  # firefox
  # gedit
  # wireshark
];
```

### macOS Setup

1. **Install XQuartz:**
   ```bash
   brew install --cask xquartz
   ```

2. **Launch XQuartz** (from Applications > Utilities, or `open -a XQuartz`)

3. **Connect with X11 forwarding:**
   ```bash
   orb -m dev ssh -X
   # Or use orbctl:
   orbctl ssh dev -- -X
   ```

4. **Run GUI apps:**
   ```bash
   # Inside the SSH session:
   firefox &
   ```

### Limitations
- No full desktop — individual windows only
- Performance depends on network latency (fine for localhost)
- Some apps may not render correctly without a full display manager

---

## Option C: noVNC (Browser-Based Desktop)

Combines VNC with a web frontend — access the desktop from any browser, no VNC client needed.

### NixOS Config

Add to `configuration.nix`:

```nix
services.xserver = {
  enable = true;
  desktopManager.xfce.enable = true;
};

# TigerVNC + noVNC
services.tigervnc.server = {
  enable = true;
  passwordFile = "/home/tvl/.vnc/passwd";
  extraArguments = [ "-geometry" "1920x1080" "-depth" "24" ];
};

# noVNC web frontend
services.novnc = {
  enable = true;
  port = 6080;
  openFirewall = true;
};
```

### Access

1. Set VNC password and rebuild (same as Option A)
2. Open browser to `http://localhost:6080/vnc.html`
3. Enter VNC password in the web UI

### Advantages
- No client software needed on macOS
- Works from any device on the network
- Good for quick access from iPad/tablet

---

## Comparison

| Approach | Full Desktop | Client Required | Disk Overhead | RAM Overhead | Complexity |
|----------|-------------|-----------------|---------------|--------------|------------|
| VNC + XFCE | Yes | VNC viewer | ~1-2 GB | ~200-400 MB | Low |
| X11 Forwarding | No (windows) | XQuartz | ~200 MB | ~50 MB | Low |
| noVNC | Yes | Browser only | ~1-2 GB | ~200-400 MB | Medium |

## Recommendation

For a **dev container**, X11 forwarding (Option B) is usually sufficient — you get GUI app windows without the overhead of a full desktop. If you need a full desktop environment for testing or development, VNC + XFCE (Option A) is the simplest setup.
