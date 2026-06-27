import sys, time, threading
from datetime import datetime
from ..fs.kernel import state

_clock_running = False
_clock_thread  = None

def update_time_display():
    last_minute = None
    while _clock_running:
        if not state.editor_open:
            current_minute = datetime.now().strftime("%H:%M")
            if current_minute != last_minute:
                last_minute = current_minute
                sys.stdout.write("\033[s\033[4;1H")
                sys.stdout.write(f"Time: [{current_minute}]" + " " * 20)
                sys.stdout.write("\033[u")
                sys.stdout.flush()
        time.sleep(1)

def start_clock():
    global _clock_running, _clock_thread
    _clock_running = True
    _clock_thread  = threading.Thread(target=update_time_display, daemon=True)
    _clock_thread.start()

def stop_clock():
    global _clock_running
    _clock_running = False
