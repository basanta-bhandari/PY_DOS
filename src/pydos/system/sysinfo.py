import os, sys, platform, shutil, subprocess, time
import psutil

_PM_RELAY = {
    'cachyos':'pacman','arch':'pacman','manjaro':'pacman','endeavouros':'pacman',
    'artix':'pacman','garuda':'pacman','ubuntu':'apt','debian':'apt',
    'linuxmint':'apt','pop':'apt','elementary':'apt','kali':'apt','raspbian':'apt',
    'fedora':'dnf','rhel':'dnf','centos':'dnf','rocky':'dnf','alma':'dnf',
    'opensuse':'zypper','suse':'zypper','alpine':'apk','macos':'brew','windows':None,
}

def detect_os_info():
    info = {'system': platform.system(), 'release': platform.release(),
            'distro': 'unknown', 'distro_name': 'Unknown'}
    if info['system'] == 'Linux':
        try:
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('ID='):
                        info['distro'] = line.split('=',1)[1].strip().strip('"').lower()
                    elif line.startswith('NAME='):
                        info['distro_name'] = line.split('=',1)[1].strip().strip('"')
        except FileNotFoundError:
            for path, distro in (('/etc/arch-release','arch'),('/etc/debian_version','debian'),
                                 ('/etc/redhat-release','rhel'),('/etc/alpine-release','alpine')):
                if os.path.exists(path):
                    info['distro'] = distro; break
    elif info['system'] == 'Darwin':
        info['distro'] = 'macos'; info['distro_name'] = 'macOS'
    elif info['system'] == 'Windows':
        info['distro'] = 'windows'; info['distro_name'] = 'Windows'
    return info

def detect_package_manager():
    info    = detect_os_info()
    distro  = info.get('distro', '')
    pm_name = next((v for k, v in _PM_RELAY.items() if k in distro), None)
    avail   = {}
    if pm_name and shutil.which(pm_name):
        avail[pm_name] = pm_name
    if not avail:
        for name in ('pacman','apt','dnf','zypper','apk','brew'):
            if shutil.which(name):
                avail[name] = name
    return {'os_info': info, 'package_managers': avail}

def _bar(pct, w=20):
    f = int(w * pct / 100)
    return '[' + '#'*f + '-'*(w-f) + f'] {pct:.1f}%'

def _fmt(b):
    for u in ('B','KB','MB','GB','TB'):
        if b < 1024: return f"{b:.1f}{u}"
        b /= 1024
    return f"{b:.1f}PB"

_LOGOS = {
    'cachyos': ("\033[1;36m", ["      ___      ","    /  __  \\   ","   /  /  \\  \\  ",
                               "  /  / C  /  / "," /___\\___/  /  ","  \\________/   ","   CachyOS     "]),
    'arch':    ("\033[1;36m", ["       /\\      ","      /  \\     ","     /\\   \\    ",
                               "    /  __  \\   ","   / /    \\ \\  ","  /_/      \\_\\ ","    Arch Linux "]),
    'ubuntu':  ("\033[1;33m", ["   _____       ","  /  __  \\     "," |  /  \\  |    ",
                               " |  \\__/  |    ","  \\______/     ","               ","    Ubuntu     "]),
    'debian':  ("\033[1;31m", ["   ______      ","  /  __   \\    "," /  /  )   |   ",
                               "|  |  (    |   "," \\  \\__)   /   ","  \\______./    ","    Debian     "]),
    'fedora':  ("\033[1;34m", ["   ______      ","  /  ____\\     "," /  /___       ",
                               "|  |_____      "," \\  \\_____|    ","  \\______/     ","    Fedora     "]),
}

def _logo(distro):
    for key, val in _LOGOS.items():
        if key in distro.lower():
            return val
    return ("\033[1;37m", ["    .---.      ","   /     \\     ","  | () () |    ",
                            "   \\  ^  /     ","    |||||      ","    |||||      ","    Linux      "])

def sysinfo_command():
    from ..display import clear_terminal
    clear_terminal()
    info = detect_os_info()
    color, logo = _logo(info['distro'])
    reset = "\033[0m"; bold = "\033[1m"
    cpu_pct  = psutil.cpu_percent(interval=0.1)
    cpu_cnt  = psutil.cpu_count()
    mem      = psutil.virtual_memory()
    disk     = psutil.disk_usage('/')
    bat      = psutil.sensors_battery()
    try:
        uptime_s = int(time.time() - psutil.boot_time())
        uptime   = f"{uptime_s//3600}h {(uptime_s%3600)//60}m"
    except Exception:
        uptime = "N/A"
    user = os.environ.get('USER') or os.environ.get('USERNAME', 'user')
    rows = [
        f"{bold}{color}{user}@{platform.node()}{reset}",
        "─" * 28,
        f"{bold}OS      {reset} {info['distro_name']} {info['release']}",
        f"{bold}Arch    {reset} {platform.machine()}",
        f"{bold}Python  {reset} {sys.version.split()[0]}",
        f"{bold}Uptime  {reset} {uptime}",
        f"{bold}Shell   {reset} PY DOS",
        "",
        f"{bold}CPU     {reset} {platform.processor() or 'N/A'}",
        f"{bold}Cores   {reset} {cpu_cnt}",
        f"{bold}CPU %   {reset} {_bar(cpu_pct)}",
        "",
        f"{bold}RAM     {reset} {_fmt(mem.used)} / {_fmt(mem.total)}",
        f"{bold}RAM %   {reset} {_bar(mem.percent)}",
        "",
        f"{bold}Disk    {reset} {_fmt(disk.used)} / {_fmt(disk.total)}",
        f"{bold}Disk %  {reset} {_bar(disk.percent)}",
    ]
    if bat:
        rows.append(f"{bold}Battery {reset} {bat.percent:.0f}% {'⚡ Charging' if bat.power_plugged else '🔋'}")
    print()
    for i in range(max(len(logo), len(rows))):
        l = f"{color}{logo[i]}{reset}" if i < len(logo) else ' ' * 16
        r = rows[i] if i < len(rows) else ''
        print(f"  {l}   {r}")
    print()
