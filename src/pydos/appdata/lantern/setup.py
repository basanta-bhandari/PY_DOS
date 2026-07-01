import subprocess
import sys
import shutil
import os
import platform
import json
import ipaddress
import time
import threading
import re

try:
    _args = _pydos_run_args_
except NameError:
    _args = ""

def is_termux():
    return 'com.termux' in os.environ.get('PREFIX', '') or os.path.exists('/data/data/com.termux')

def find_yggdrasil_address():
    # Primary: ask yggdrasilctl directly
    if shutil.which('yggdrasilctl'):
        try:
            result = subprocess.run(
                ['sudo', 'yggdrasilctl', 'getself'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if 'IPv6 address' in line:
                    parts = line.split('│')
                    for p in parts:
                        p = p.strip()
                        if p and ':' in p and not p.startswith('IPv6'):
                            return p
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Fallback: /proc/net/if_inet6
    try:
        with open('/proc/net/if_inet6') as f:
            for line in f:
                fields = line.split()
                if not fields or len(fields[0]) != 32:
                    continue
                raw = bytes.fromhex(fields[0])
                if (raw[0] & 0xFE) == 0x02:
                    addr = str(ipaddress.IPv6Address(raw))
                    if not addr.startswith('fe'):
                        return addr
    except (FileNotFoundError, PermissionError, ValueError):
        pass

    return None

_PM_RELAY = {
    'cachyos':      'pacman',
    'arch':         'pacman',
    'manjaro':      'pacman',
    'endeavouros':  'pacman',
    'artix':        'pacman',
    'garuda':       'pacman',
    'ubuntu':       'apt',
    'debian':       'apt',
    'linuxmint':    'apt',
    'pop':          'apt',
    'elementary':   'apt',
    'kali':         'apt',
    'raspbian':     'apt',
    'fedora':       'dnf',
    'rhel':         'dnf',
    'centos':       'dnf',
    'rocky':        'dnf',
    'alma':         'dnf',
    'opensuse':     'zypper',
    'suse':         'zypper',
    'alpine':       'apk',
    'macos':        'brew',
    'windows':      None,
}

def _detect_os_info():
    os_info = {
        'system':      platform.system(),
        'release':     platform.release(),
        'distro':      'unknown',
        'distro_name': 'Unknown',
    }
    if os_info['system'] == 'Linux':
        try:
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('ID='):
                        os_info['distro'] = line.split('=',1)[1].strip().strip('"').lower()
                    elif line.startswith('NAME='):
                        os_info['distro_name'] = line.split('=',1)[1].strip().strip('"')
        except FileNotFoundError:
            for path, distro in (
                ('/etc/arch-release',   'arch'),
                ('/etc/debian_version', 'debian'),
                ('/etc/redhat-release', 'rhel'),
                ('/etc/SuSE-release',   'opensuse'),
                ('/etc/alpine-release', 'alpine'),
            ):
                if os.path.exists(path):
                    os_info['distro'] = distro
                    break
    elif os_info['system'] == 'Darwin':
        os_info['distro'] = 'macos'
        os_info['distro_name'] = 'macOS'
    elif os_info['system'] == 'Windows':
        os_info['distro'] = 'windows'
        os_info['distro_name'] = 'Windows'
    return os_info

def _detect_package_manager():
    os_info = _detect_os_info()
    distro  = os_info.get('distro', 'unknown')

    pm_name = None
    for key in _PM_RELAY:
        if key in distro:
            pm_name = _PM_RELAY[key]
            break

    available = {}
    if pm_name:
        cmd = pm_name
        if shutil.which(cmd):
            available[pm_name] = cmd

    if not available:
        for name, cmd in {'pacman':'pacman','apt':'apt','dnf':'dnf',
                          'zypper':'zypper','apk':'apk','brew':'brew'}.items():
            if shutil.which(cmd):
                available[name] = cmd

    return {'os_info': os_info, 'package_managers': available}

def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, **kw)

_sudo_cached = False

def cache_sudo():
    global _sudo_cached
    if _sudo_cached:
        return True
    print("\n[Sudo Caching]")
    resp = input("Cache sudo credentials for this session? (y/N): ").strip().lower()
    if resp not in ('y', 'yes'):
        print("Skipping sudo cache.")
        return False
    if subprocess.run(['sudo', '-v']).returncode != 0:
        print("[!] Failed to authenticate sudo.")
        return False

    def _keepalive():
        while True:
            time.sleep(50)
            try:
                if subprocess.run(['sudo', '-n', 'true'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL).returncode != 0:
                    break
            except OSError:
                break

    threading.Thread(target=_keepalive, daemon=True).start()
    _sudo_cached = True
    print("[✓] Sudo credentials cached.")
    return True

def install_via_github_deb():
    arch_map = {'x86_64':'amd64','aarch64':'arm64','armv7l':'armhf','i686':'386'}
    deb_arch = arch_map.get(platform.machine())
    if not deb_arch:
        print(f"[!] Unknown arch '{platform.machine()}'")
        return False
    print("[Lantern] Fetching latest Yggdrasil release from GitHub...")
    r = run(['curl','-fsSL',
             'https://api.github.com/repos/yggdrasil-network/yggdrasil-go/releases/latest'],
            capture_output=True, text=True)
    if r.returncode != 0:
        print("[!] Couldn't reach GitHub.")
        return False
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return False
    url = next((a['browser_download_url'] for a in data.get('assets',[])
                if a['name'].endswith('.deb') and deb_arch in a['name']), None)
    if not url:
        print(f"[!] No .deb found for {deb_arch}.")
        return False
    run(['curl','-fsSL','-o','/tmp/yggdrasil.deb', url])
    run(['sudo','dpkg','-i','/tmp/yggdrasil.deb'])
    run(['sudo','apt-get','install','-f','-y'])
    return shutil.which('yggdrasil') is not None

def setup_desktop():
    # ── 1. Install ────────────────────────────────────────────────────────
    if not (shutil.which('yggdrasilctl') or shutil.which('yggdrasil')):
        print("[Lantern] Yggdrasil not found. Installing...")
        cache_sudo()
        detected = _detect_package_manager()
        pms      = detected['package_managers']
        ok       = False

        if 'pacman' in pms:
            ok = run(['sudo','pacman','-S','--needed','--noconfirm','yggdrasil']).returncode == 0
        elif 'dnf' in pms:
            run(['sudo','dnf','-y','copr','enable','rany/yggdrasil'])
            ok = run(['sudo','dnf','-y','install','yggdrasil']).returncode == 0
        elif 'zypper' in pms:
            ok = run(['sudo','zypper','--non-interactive','install','yggdrasil']).returncode == 0
        elif 'apk' in pms:
            ok = run(['sudo','apk','add','yggdrasil']).returncode == 0
        elif 'apt' in pms:
            ok = install_via_github_deb()
        else:
            print("[!] No supported package manager found.")
            print("Manual: https://yggdrasil-network.github.io/installation.html")
            return

        if not ok:
            print("[!] Install failed.")
            print("Manual: https://yggdrasil-network.github.io/installation.html")
            return
    else:
        print("[Lantern] Yggdrasil already installed.")

    # ── 2. Generate config if missing ─────────────────────────────────────
    conf_path = '/etc/yggdrasil.conf'
    if not os.path.exists(conf_path):
        print("[Lantern] Generating default config...")
        result = subprocess.run(
            ['yggdrasil', '-genconf'],
            capture_output=True, text=True
        )
        subprocess.run(
            ['sudo', 'tee', conf_path],
            input=result.stdout, capture_output=True, text=True
        )

    # ── 3. Enable + start ─────────────────────────────────────────────────
    if shutil.which('systemctl'):
        status = subprocess.run(
            ['systemctl','is-active','yggdrasil'],
            capture_output=True, text=True
        ).stdout.strip()
        if status != 'active':
            print("[Lantern] Starting Yggdrasil service...")
            run(['sudo','systemctl','enable','--now','yggdrasil'])
            time.sleep(2)
        else:
            print("[Lantern] Service is running.")

    # ── 4. Your address ───────────────────────────────────────────────────
    my_addr = find_yggdrasil_address()
    if not my_addr:
        print("[!] No Yggdrasil address detected yet.")
        print("    Try: sudo systemctl status yggdrasil")
        return

    print(f"""
╔══════════════════════════════════════════════════════╗
║              YOUR YGGDRASIL ADDRESS                  ║
╠══════════════════════════════════════════════════════╣
║  [{my_addr}]
║                                                      ║
║  Share this with anyone you want to chat with.       ║
║  They need to run setup and add your address too.    ║
╚══════════════════════════════════════════════════════╝
""")

    # ── 5. Peer setup ─────────────────────────────────────────────────────
    while True:
        ans = input("Add a peer now? (y/N): ").strip().lower()
        if ans not in ('y', 'yes'):
            break

        peer_addr = input("Paste their Yggdrasil address: ").strip().strip('[]')
        if not peer_addr:
            print("No address entered.")
            break

        try:
            ipaddress.IPv6Address(peer_addr)
        except ValueError:
            print(f"[!] '{peer_addr}' is not a valid IPv6 address. Try again.")
            continue

        peer_uri = f"tcp://[{peer_addr}]:9001"

        try:
            with open(conf_path) as f:
                conf = f.read()
        except PermissionError:
            conf = subprocess.run(
                ['sudo','cat',conf_path], capture_output=True, text=True
            ).stdout

        if peer_addr in conf:
            print(f"[✓] {peer_addr} is already in your peer list.")
        else:
            new_conf = re.sub(
                r'Peers:\s*\[([^\]]*)\]',
                lambda m: 'Peers: [' + (m.group(1).strip() + ', ' if m.group(1).strip() else '') + f'"{peer_uri}"]',
                conf
            )
            if new_conf == conf:
                new_conf += f'\nPeers: ["{peer_uri}"]\n'

            proc = subprocess.run(
                ['sudo','tee',conf_path],
                input=new_conf, capture_output=True, text=True
            )
            if proc.returncode == 0:
                print(f"[✓] Peer added.")
                run(['sudo','systemctl','restart','yggdrasil'])
                time.sleep(2)
                if find_yggdrasil_address():
                    print("[✓] Yggdrasil restarted OK.")
                else:
                    print("[!] Restarted but address not visible yet, give it a moment.")
            else:
                print(f"[!] Failed to write config: {proc.stderr}")

        ans2 = input("Add another peer? (y/N): ").strip().lower()
        if ans2 not in ('y', 'yes'):
            break

    # ── 6. Done ───────────────────────────────────────────────────────────
    print(f"""
[Lantern] All set.

  Your address : [{my_addr}]
  Commands     :
    run community host   → start a lobby
    run community        → find / join one
""")

def setup_termux():
    print("[Lantern] Termux can't open a TUN device without root.")
    print("Install the Yggdrasil Android app instead:")
    print("  F-Droid : https://f-droid.org/packages/eu.neilalexander.yggdrasil/")
    print("  GitHub  : https://github.com/yggdrasil-network/yggdrasil-android/releases")
    input("\nPress ENTER once the app shows it's connected... ")
    addr = find_yggdrasil_address()
    if addr:
        print(f"[Lantern] Your address: [{addr}]")
    else:
        print("[!] Couldn't detect address — copy it from inside the app.")
    print("\nRun: run community")

def main():
    print("=== LANTERN SETUP ===\n")
    if is_termux():
        setup_termux()
        return
    sys_info = _detect_os_info()
    if sys_info['system'] == 'Darwin':
        print("[Lantern] macOS: https://yggdrasil-network.github.io/installation-mac.html")
        addr = find_yggdrasil_address()
        if addr:
            print(f"Your address: [{addr}]")
        if shutil.which('yggdrasil'):
            setup_desktop()
    elif sys_info['system'] == 'Windows':
        print("[Lantern] Windows: https://yggdrasil-network.github.io/installation-windows.html")
    else:
        setup_desktop()

main()
