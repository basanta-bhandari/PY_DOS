import os, sys, time
import psutil
from datetime import datetime

PY_DOS = """
\n
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
\n
"""

def clear_terminal():
    os.system('cls' if sys.platform.startswith('win') else 'clear')

def get_battery_status():
    battery = psutil.sensors_battery()
    if battery is None:
        print("Battery: [####################] 100% ⚡ | Desktop")
        return
    pct    = int(battery.percent)
    filled = int(pct / 5)
    bar    = '#' * filled + ':' * (20 - filled)
    icon   = "⚡" if battery.power_plugged else "🔋"
    if battery.secsleft == psutil.POWER_TIME_UNLIMITED:
        time_str = "Charging"
    elif battery.secsleft == psutil.POWER_TIME_UNKNOWN:
        time_str = "Unknown"
    else:
        m, s = divmod(battery.secsleft, 60)
        h, m = divmod(m, 60)
        time_str = f"{int(h)}h {int(m)}m"
    print(f"Battery: [{bar}] {pct}% {icon}")
    print(f"Time Left: {time_str}")

def display_loading_screen():
    from .fs.persistence import load_filesystem
    from .system.auth import display_lockscreen
    clear_terminal()
    print(PY_DOS)
    print("\nLoading filesystem...")
    print("=" * 32)
    clear_terminal()
    bar = 40
    for i in range(bar + 1):
        print(f"\r[{'#'*i + ':'*(bar-i)}]", end="", flush=True)
        time.sleep(0.05)
    print("\n")
    load_filesystem()
    time.sleep(0.5)
    display_lockscreen()

def display_home():
    from .system.clock import start_clock
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version 0.1.0-beta]")
    print("ENTER 'help' TO GET STARTED.")
    get_battery_status()
    print(f"Time: {datetime.now().strftime('%H:%M')}")
    start_clock()

def get_current_path():
    from .fs.kernel import state
    return state.current_directory.replace('/', '\\') if state.current_directory != '/' else '\\'

def check_input():
    return input(f"PY DOS {get_current_path()}> ")
