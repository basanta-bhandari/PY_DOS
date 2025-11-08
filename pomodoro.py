import os
import sys
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

DATA_FILE = os.path.expanduser("~/.pomodoro_data")
CONFIG_FILE = os.path.expanduser("~/.pomodoro_config")
PRESETS_FILE = os.path.expanduser("~/.pomodoro_presets")

DEFAULT_CONFIG = {
    "work_time": 25,
    "break_time": 5,
    "long_break": 15,
    "sessions_until_long": 4,
    "auto_continue": False,
    "sound_enabled": True,
    "daily_goal": 8
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_presets():
    if os.path.exists(PRESETS_FILE):
        with open(PRESETS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_presets(presets):
    with open(PRESETS_FILE, 'w') as f:
        json.dump(presets, f, indent=2)

def log_session(start, duration, work=True, task=None, tags=None):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'a') as f:
        entry = {
            'start': str(start),
            'end': str(start + timedelta(seconds=duration)),
            'duration': duration,
            'type': 'work' if work else 'break',
            'task': task,
            'tags': tags or []
        }
        f.write(json.dumps(entry) + '\n')

def parse_data():
    if not os.path.exists(DATA_FILE):
        return []
    data = []
    with open(DATA_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entry['start'] = datetime.strptime(entry['start'], '%Y-%m-%d %H:%M:%S.%f')
                data.append(entry)
            except:
                continue
    return data

def play_sound():
    try:
        if sys.platform == 'darwin':
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        elif sys.platform.startswith('linux'):
            os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || beep')
        elif sys.platform == 'win32':
            import winsound
            winsound.Beep(1000, 500)
    except:
        print('\a')

def run_timer(minutes, label, config):
    remaining = minutes * 60
    print(f"\n{label}: {minutes}min")
    
    try:
        while remaining > 0:
            mins, secs = divmod(remaining, 60)
            print(f"\r{mins:02d}:{secs:02d}", end="", flush=True)
            time.sleep(1)
            remaining -= 1
        
        print(f"\n{label} complete!")
        if config.get('sound_enabled', True):
            play_sound()
        return True
    except KeyboardInterrupt:
        print("\nTimer paused")
        return False

def timer(work_time=None, break_time=None, long_break=None, sessions=None, 
         auto_continue=None, task=None, tags=None):
    
    config = load_config()
    
    work_time = work_time or config['work_time']
    break_time = break_time or config['break_time']
    long_break = long_break or config['long_break']
    sessions_until_long = sessions or config['sessions_until_long']
    auto_continue = auto_continue if auto_continue is not None else config['auto_continue']
    
    session_count = 0
    
    print(f"Starting Pomodoro Timer")
    if task:
        print(f"Task: {task}")
    if tags:
        print(f"Tags: {', '.join(tags)}")
    print(f"Work: {work_time}min | Break: {break_time}min | Long break: {long_break}min")
    print(f"Press Ctrl+C to pause/stop\n")
    
    try:
        while True:
            session_count += 1
            start = datetime.now()
            
            if run_timer(work_time, f"Work Session {session_count}", config):
                log_session(start, work_time * 60, True, task, tags)
            else:
                break
            
            if session_count % sessions_until_long == 0:
                break_duration = long_break
                break_label = "Long Break"
            else:
                break_duration = break_time
                break_label = "Short Break"
            
            if not auto_continue:
                input(f"\nPress Enter to start {break_label}...")
            
            start = datetime.now()
            if run_timer(break_duration, break_label, config):
                log_session(start, break_duration * 60, False, task, tags)
            else:
                break
            
            if not auto_continue:
                input("\nPress Enter to start next work session...")
                
    except KeyboardInterrupt:
        print("\nPomodoro stopped")

def stats(period='today', task=None, tags=None):
    data = parse_data()
    
    if task:
        data = [s for s in data if s.get('task') == task]
    if tags:
        data = [s for s in data if any(t in s.get('tags', []) for t in tags)]
    
    if not data:
        print("No data found")
        return
    
    work_data = [s for s in data if s['type'] == 'work']
    
    if period == 'today':
        today = datetime.now().date()
        hours = sum(s['duration'] for s in work_data if s['start'].date() == today) / 3600
        sessions = len([s for s in work_data if s['start'].date() == today])
        print(f"Today: {hours:.1f}h ({sessions} sessions)")
        
    elif period == 'week':
        week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
        week_data = defaultdict(lambda: {'hours': 0, 'sessions': 0})
        
        for s in work_data:
            if s['start'].date() >= week_start:
                day = s['start'].date()
                week_data[day]['hours'] += s['duration'] / 3600
                week_data[day]['sessions'] += 1
        
        if week_data:
            print("\nThis week:")
            for day in sorted(week_data.keys()):
                info = week_data[day]
                print(f"{day}: {info['hours']:.1f}h ({info['sessions']} sessions)")
        else:
            print("No data for this week")
            
    elif period == 'total':
        total = sum(s['duration'] for s in work_data) / 3600
        sessions = len(work_data)
        print(f"Total: {total:.1f}h ({sessions} sessions)")
        
    elif period == 'tasks':
        task_data = defaultdict(lambda: {'hours': 0, 'sessions': 0})
        for s in work_data:
            if s.get('task'):
                task_data[s['task']]['hours'] += s['duration'] / 3600
                task_data[s['task']]['sessions'] += 1
        
        if task_data:
            print("\nBy task:")
            for task, info in sorted(task_data.items(), key=lambda x: x[1]['hours'], reverse=True):
                print(f"{task}: {info['hours']:.1f}h ({info['sessions']} sessions)")
        else:
            print("No task data found")

def goal_set(hours):
    config = load_config()
    config['daily_goal'] = hours
    save_config(config)
    print(f"Daily goal set to {hours}h")

def goal_check():
    config = load_config()
    data = parse_data()
    today = datetime.now().date()
    
    work_data = [s for s in data if s['type'] == 'work' and s['start'].date() == today]
    hours = sum(s['duration'] for s in work_data) / 3600
    goal = config['daily_goal']
    
    print(f"Today: {hours:.1f}h / {goal}h ({hours/goal*100:.1f}%)")
    if hours >= goal:
        print("Goal achieved!")
    else:
        remaining = goal - hours
        print(f"Remaining: {remaining:.1f}h")

def preset_save(name, work, break_time, long_break, sessions):
    presets = load_presets()
    presets[name] = {
        'work_time': work,
        'break_time': break_time,
        'long_break': long_break,
        'sessions_until_long': sessions
    }
    save_presets(presets)
    print(f"Preset '{name}' saved")

def preset_use(name):
    presets = load_presets()
    if name not in presets:
        print(f"Preset '{name}' not found")
        return
    
    preset = presets[name]
    timer(**preset)

def preset_list():
    presets = load_presets()
    if not presets:
        print("No presets saved")
        return
    
    print("Saved presets:")
    for name, settings in presets.items():
        print(f"  {name}: {settings['work_time']}m work, {settings['break_time']}m break")

def main():
    if len(sys.argv) < 2:
        timer()
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'start':
        args = sys.argv[2:]
        kwargs = {}
        
        i = 0
        while i < len(args):
            if args[i] == '--work' and i + 1 < len(args):
                kwargs['work_time'] = int(args[i + 1])
                i += 2
            elif args[i] == '--break' and i + 1 < len(args):
                kwargs['break_time'] = int(args[i + 1])
                i += 2
            elif args[i] == '--long-break' and i + 1 < len(args):
                kwargs['long_break'] = int(args[i + 1])
                i += 2
            elif args[i] == '--sessions' and i + 1 < len(args):
                kwargs['sessions'] = int(args[i + 1])
                i += 2
            elif args[i] == '--task' and i + 1 < len(args):
                kwargs['task'] = args[i + 1]
                i += 2
            elif args[i] == '--tags' and i + 1 < len(args):
                kwargs['tags'] = args[i + 1].split(',')
                i += 2
            elif args[i] == '--auto':
                kwargs['auto_continue'] = True
                i += 1
            else:
                i += 1
        
        timer(**kwargs)
        
    elif cmd == 'stats':
        period = sys.argv[2] if len(sys.argv) > 2 else 'today'
        stats(period)
        
    elif cmd == 'goal':
        if len(sys.argv) < 3:
            goal_check()
        elif sys.argv[2] == 'set' and len(sys.argv) > 3:
            goal_set(float(sys.argv[3]))
        elif sys.argv[2] == 'check':
            goal_check()
            
    elif cmd == 'preset':
        if len(sys.argv) < 3:
            preset_list()
        elif sys.argv[2] == 'save' and len(sys.argv) >= 8:
            preset_save(sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), 
                       int(sys.argv[6]), int(sys.argv[7]))
        elif sys.argv[2] == 'use' and len(sys.argv) > 3:
            preset_use(sys.argv[3])
        elif sys.argv[2] == 'list':
            preset_list()
    
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()