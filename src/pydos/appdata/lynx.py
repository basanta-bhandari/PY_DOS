import subprocess
import sys
import shutil
import platform

try:
    url = _pydos_run_args_
except NameError:
    url = ""

def _detect_pkg_manager():
    managers = [
        ("apt-get", ["sudo", "apt-get", "install", "-y", "lynx"]),
        ("apt",     ["sudo", "apt",     "install", "-y", "lynx"]),
        ("pacman",  ["sudo", "pacman",  "-S",      "--noconfirm", "lynx"]),
        ("dnf",     ["sudo", "dnf",     "install", "-y", "lynx"]),
        ("brew",    ["brew", "install", "lynx"]),
        ("zypper",  ["sudo", "zypper",  "install", "-y", "lynx"]),
    ]
    for bin_name, cmd in managers:
        if shutil.which(bin_name):
            return cmd
    return None

def _print_manual_instructions():
    print("\\n[Lynx] Could not install automatically. Manual instructions:")
    print("-" * 54)
    import platform as _p
    s = _p.system()
    if s == "Linux":
        print("  Debian/Ubuntu : sudo apt install lynx")
        print("  Arch          : sudo pacman -S lynx")
        print("  Fedora/RHEL   : sudo dnf install lynx")
        print("  openSUSE      : sudo zypper install lynx")
    elif s == "Darwin":
        print("  macOS (Homebrew): brew install lynx")
    elif s == "Windows":
        print("  Windows: winget install lynx")
        print("           or: https://lynx.invisible-island.net/")
    else:
        print("  Visit: https://lynx.invisible-island.net/")
    print("-" * 54)

if shutil.which("lynx") is None:
    print("[Lynx] Lynx not found. Attempting to install...")
    install_cmd = _detect_pkg_manager()
    if install_cmd is None:
        print("[Lynx] No supported package manager found.")
        _print_manual_instructions()
    else:
        print(f"[Lynx] Running: {chr(32).join(install_cmd)}")
        result = subprocess.run(install_cmd)
        if result.returncode != 0 or shutil.which("lynx") is None:
            print("[Lynx] Automatic installation failed (permissions issue?).")
            _print_manual_instructions()
        else:
            print("[Lynx] Lynx installed successfully.")

if shutil.which("lynx"):
    cmd = ["lynx"]
    if url and url.strip():
        target = url.strip()
        if not target.startswith(("http://", "https://")):
            target = "https://" + target
        cmd.append(target)
    subprocess.run(cmd)
else:
    print("[Lynx] Lynx unavailable. Cannot launch browser.")