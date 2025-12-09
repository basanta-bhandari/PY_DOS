import time
import sys
import random
import os
import platform
import json
import readline
import readchar
import atexit
import pickle
from pathlib import Path
import types
import tempfile
import psutil
from datetime import datetime
import threading

FILESYSTEM_FILE = 'pydos_filesystem.json'
SAVED_FOLDER = 'saved'


directory_contents = {}
current_directory = '/'
kernel = {
    '/': {
        'type': 'directory',
        'contents': {
            'bin': {'type': 'directory', 'contents': {}},
            'usr': {'type': 'directory', 'contents': {}},
            'tmp': {'type': 'directory', 'contents': {}},
            'Apps': {
                'type': 'directory',
                'contents': {
                    'Productivity': {'type': 'directory', 'contents': {
                        'Pomodoro': {'type': 'directory', 'contents': {}}
                    }},
                    'Games': {'type': 'directory', 'contents': {}},
                    'Utilities': {'type': 'directory', 'contents': {}}
                }
            }
        }
    }
}
PY_DOS = """
\n
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

def display_loading_screen():
    clear_terminal()
    print(PY_DOS)
    print("\nLoading filesystem...")
    
    bar_width = 40
    for i in range(bar_width + 1):   
        progress = "#" * i + ":" * (bar_width - i)
        print(f"\r[{progress}]", end="", flush=True)
        time.sleep(0.05)
    
    print("\n")
    load_filesystem()
    time.sleep(0.5)

def display_home():
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version Beta]")
    print("ENTER 'help' TO GET STARTED.")
    print("="*50)
    get_battery_status()
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"Time: {current_time}")
    print()

def get_current_path():
    return current_directory.replace('/', '\\') if current_directory != '/' else '\\'

def check_input():
    return input(f"PY DOS {get_current_path()}> ")

def normalize_path(path):
    if path.startswith('/'):
        parts = path.strip('/').split('/')
    else:
        parts = current_directory.strip('/').split('/')
        if current_directory == '/':
            parts = []
        parts.extend(path.split('/'))
    
    normalized = []
    for part in parts:
        if part == '..':
            if normalized:
                normalized.pop()
        elif part and part != '.':
            normalized.append(part)
    
    return '/' + '/'.join(normalized) if normalized else '/'

def join_path(base, name):
    if base == '/':
        return '/' + name
    return base + '/' + name

def ensure_saved_folder():
    Path(SAVED_FOLDER).mkdir(exist_ok=True)

def save_file_contents():
    try:
        ensure_saved_folder()
        file_path = Path(SAVED_FOLDER) / 'file_contents.bin'
        with open(file_path, 'wb') as f:
            pickle.dump(directory_contents, f)
    except Exception as e:
        print(f"Error saving file contents: {e}")

def load_file_contents():
    global directory_contents
    try:
        file_path = Path(SAVED_FOLDER) / 'file_contents.bin'
        if file_path.exists():
            with open(file_path, 'rb') as f:
                directory_contents = pickle.load(f)
        else:
            directory_contents = {}
    except Exception as e:
        print(f"Error loading file contents: {e}")
        directory_contents = {}

def save_filesystem():
    try:
        save_data = {'kernel': kernel, 'current_directory': current_directory}
        
        history = []
        try:
            for i in range(readline.get_current_history_length()):
                history.append(readline.get_history_item(i + 1))
            save_data['command_history'] = history[-10:]
        except:
            save_data['command_history'] = []
            
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        save_file_contents()
        print("State : NS [N/E]")
    except Exception as e:
        print(f"Error saving filesystem: {e}")
        
def load_filesystem():
    global kernel, current_directory
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            kernel = save_data.get('kernel', kernel)
            current_directory = save_data.get('current_directory', '/')
            load_file_contents()
            print("Filesystem loaded from previous session.")
        else:
            print("State: CS [N/E]")
    except Exception as e:
        print(f"State: SS [E/E]  ----> CS")

def get_battery_status():
    battery = psutil.sensors_battery()
    if battery is None:
        print("Battery: [################] 100% ⚡ | Desktop")
        return

    percent = int(battery.percent)
    filled = int(percent / 5)
    empty = 20 - filled
    bar = "#" * filled + ":" * empty
    
    icon = "⚡" if battery.power_plugged else ""
    
    if battery.secsleft == psutil.POWER_TIME_UNLIMITED:
        time_str = "Charging"
    elif battery.secsleft == psutil.POWER_TIME_UNKNOWN:
        time_str = "Unknown"
    else:
        minutes, seconds = divmod(battery.secsleft, 60)
        hours, minutes = divmod(minutes, 60)
        time_str = f"{int(hours)}h {int(minutes)}m"
    
    print(f"Battery: [{bar}] {percent}% {icon}")
    print(f"Time Left: {time_str}")

def get_cpu_stats():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_count = psutil.cpu_count()
    return cpu_percent, cpu_count

def get_memory_stats():
    memory = psutil.virtual_memory()
    return memory.percent, memory.used, memory.total

def get_disk_stats():
    disk = psutil.disk_usage('/')
    return disk.percent, disk.used, disk.total

def get_gpu_stats():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            return [(gpu.name, gpu.load * 100, gpu.memoryUsed, gpu.memoryTotal) for gpu in gpus]
    except:
        pass
    return None

def format_bytes(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f}PB"

        
def install_command(args):
    if not args:
        print("Usage: install <package_name>")
        return
    
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', args], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)

def uninstall_command(args):
    if not args:
        print("Usage: uninstall <package_name>")
        return
    
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', args], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)

def cd_command(args):
    global current_directory
    if not args:
        print(current_directory)
        return
    
    if args == '..':
        if current_directory == '/':
            return
        parts = current_directory.rstrip('/').split('/')
        current_directory = '/'.join(parts[:-1]) or '/'
        return
    
    if args == '/':
        current_directory = '/'
        return
    
    if args.startswith('/'):
        target_path = args
    else:
        target_path = current_directory.rstrip('/') + '/' + args if current_directory != '/' else '/' + args
    
    target_path = target_path.rstrip('/')
    if target_path == '':
        target_path = '/'
    
    parts = target_path.strip('/').split('/') if target_path != '/' else []
    current_node = kernel['/']
    
    for part in parts:
        if 'contents' in current_node and part in current_node['contents'] and current_node['contents'][part]['type'] == 'directory':
            current_node = current_node['contents'][part]
        else:
            print(f"Directory not found: {args}")
            return
    
    current_directory = target_path
    save_filesystem()

def mkdir_command(args):
    if not args:
        print("Usage: mkdir <directory_name>")
        return
        
    dirname = args
    new_path = normalize_path(dirname)
    
    if new_path in kernel:
        print(f"Directory '{dirname}' already exists")
        return
    
    parent_path = '/'.join(new_path.split('/')[:-1]) or '/'
    
    if parent_path == '/':
        parent_node = kernel['/']
    else:
        parts = parent_path.strip('/').split('/')
        parent_node = kernel['/']
        for part in parts:
            if 'contents' in parent_node and part in parent_node['contents']:
                parent_node = parent_node['contents'][part]
            else:
                print("Parent directory not found.")
                return
    
    dir_name_only = new_path.split('/')[-1]
    kernel[new_path] = {'type': 'directory', 'contents': {}}
    parent_node['contents'][dir_name_only] = {'type': 'directory', 'contents': {}}
    save_filesystem()
    print(f"Directory '{dirname}' created")

def rmdir_command(args):
    if not args:
        print("Usage: rmdir <directory_name>")
        return
    
    dirname = args
    target_path = normalize_path(dirname)
    
    if target_path not in kernel or kernel[target_path]['type'] != 'directory':
        print("Directory not found")
        return
    
    if kernel[target_path]['contents']:
        print("Directory is not empty")
        return
    
    del kernel[target_path]
    parent_path = '/'.join(target_path.split('/')[:-1]) or '/'
    if parent_path in kernel:
        dir_name_only = target_path.split('/')[-1]
        if dir_name_only in kernel[parent_path]['contents']:
            del kernel[parent_path]['contents'][dir_name_only]
    save_filesystem()

def ls_command():
    if current_directory == '/':
        current_node = kernel['/']
    else:
        parts = current_directory.strip('/').split('/')
        current_node = kernel['/']
        for part in parts:
            if 'contents' in current_node and part in current_node['contents']:
                current_node = current_node['contents'][part]
            else:
                print("Current directory not found.")
                return
    
    if 'contents' not in current_node:
        print("Directory is empty")
        return
    
    contents = current_node['contents']
    if not contents:
        print("Directory is empty")
    else:
        print(f"Directory of {current_directory}" if current_directory != "/" else "")
        print()
        for name, item in contents.items():
            if item['type'] == 'directory':
                print(f"<DIR>          {name}")
            else:
                print(f"<FILE>         {name}")

def rem_command(args):
    if not args or " to " not in args:
        print("Usage: rem <originalname> to <newname>")
        return
    
    parts = args.split(" to ")
    file_name = parts[0].strip()
    new_file_name = parts[1].strip()
    
    file_path = join_path(current_directory, file_name)
    new_file_path = join_path(current_directory, new_file_name)

    if file_path not in directory_contents:
        print("File not found.")
        return

    if new_file_path in directory_contents:
        print("File already exists.")
        return
    
    directory_contents[new_file_path] = directory_contents[file_path]
    del directory_contents[file_path]
    del kernel[current_directory]['contents'][file_name]
    kernel[current_directory]['contents'][new_file_name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()
    print(f"'{file_name}' renamed to '{new_file_name}' successfully.")

def mktf_command(args):
    if not args:
        print("Usage: mktf <filename>")
        return
    
    file_name = args
    file_path = join_path(current_directory, file_name)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = f.name
    
  
    
    print("\nCreating text file...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save and exit | ':q!' to exit without saving")
    input("Press ENTER to continue...")
    
    if sys.platform.startswith('win'):
        os.system(f"notepad {temp_path}")
    else:
        os.system(f"nvim {temp_path}")
    
 
    
    with open(temp_path, 'r') as f:
        content = f.read()
    
    directory_contents[file_path] = {
        'type': 'txt',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
    
    os.unlink(temp_path)
    save_file_contents()
    save_filesystem()
    print(f"Text file '{file_name}' created successfully.")

def mkef_command(args):
    if not args:
        print("Usage: mkef <filename>")
        return
    
    file_name = args
    file_path = join_path(current_directory, file_name)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_path = f.name
    


    
    print("\nCreating executable file...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save and exit | ':q!' to exit without saving")
    input("Press ENTER to continue...")
    
    if sys.platform.startswith('win'):
        os.system(f"notepad {temp_path}")
    else:
        os.system(f"nvim {temp_path}")
    
 
    
    with open(temp_path, 'r') as f:
        content = f.read()
    
    directory_contents[file_path] = {
        'type': 'exe',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
    
    os.unlink(temp_path)
    save_file_contents()
    save_filesystem()
    print(f"Executable file '{file_name}' created successfully.")

def rm_command(args):
    if not args:
        print("Usage: rm <filename>")
        return
    
    if args == 'all':
        if current_directory in kernel:
            files_to_remove = [name for name, item in kernel[current_directory]['contents'].items() if item['type'] == 'file']
            for file_name in files_to_remove:
                file_path = join_path(current_directory, file_name)
                if file_path in directory_contents:
                    del directory_contents[file_path]
                del kernel[current_directory]['contents'][file_name]
            save_file_contents()
            save_filesystem()
            print("All files removed")
        return
    
    file_path = join_path(current_directory, args)
    if file_path in directory_contents:
        del directory_contents[file_path]
        if current_directory in kernel and args in kernel[current_directory]['contents']:
            del kernel[current_directory]['contents'][args]
        save_file_contents()
        save_filesystem()
        print(f"File '{args}' deleted.")
    else:
        print("File not found.")

def copy_command(args):    
    if not args or ' to ' not in args:
        print("Usage: copy <filename> to <directory>")
        return
    
    parts = args.split(' to ')
    file_name = parts[0].strip()
    target_path = parts[1].strip()
    source_path = join_path(current_directory, file_name)

    if source_path not in directory_contents:
        print("Source file not found")
        return

    target_path = normalize_path(target_path)
    if target_path not in kernel:
        print("Target directory not found")
        return

    content = directory_contents[source_path]
    target_file_path = join_path(target_path, file_name)
    directory_contents[target_file_path] = {
        'type': directory_contents[source_path]['type'],
        'content': content['content'],
        'created_in': target_path
    }
    
    kernel[target_path]['contents'][file_name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()
    print(f"File '{file_name}' copied to {target_path} successfully.")

def move_command(args):
    if not args or ' to ' not in args:
        print("Usage: move <filename> to <directory>")
        return
    
    parts = args.split(' to ')
    file_name = parts[0].strip()
    target_path = parts[1].strip()
    source_path = join_path(current_directory, file_name)

    if source_path not in directory_contents:
        print("Source file not found")
        return

    target_path = normalize_path(target_path)
    if target_path not in kernel:
        print("Target directory not found")
        return

    content = directory_contents[source_path]  
    target_file_path = join_path(target_path, file_name)
    
    directory_contents[target_file_path] = {
        'type': directory_contents[source_path]['type'],
        'content': content['content'],
        'created_in': target_path
    }
    del directory_contents[source_path]
    del kernel[current_directory]['contents'][file_name]
    kernel[target_path]['contents'][file_name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()
    print(f"File '{file_name}' moved to {target_path} successfully.")

def edit_command(args):
    if not args:
        print("Usage: edit <filename>")
        return
    
    file_path = join_path(current_directory, args)
    if file_path not in directory_contents:
        print("File not found.")
        return
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(directory_contents[file_path]['content'])
        temp_path = f.name
    
    
    
    print("\nOpening editor...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save and exit | ':q!' to exit without saving")
    input("Press ENTER to continue...")
    
    if sys.platform.startswith('win'):
        os.system(f"notepad {temp_path}")
    else:
        os.system(f"nvim {temp_path}")
 
    
    with open(temp_path, 'r') as f:
        directory_contents[file_path]['content'] = f.read()
    
    os.unlink(temp_path)
    save_file_contents()
    save_filesystem()
    print(f"Saved '{args}'")

def vwtf_command(args):
    if not args:
        print("Usage: vwtf <filename>")
        return
        
    file_path = join_path(current_directory, args)
    if file_path in directory_contents:
        print(directory_contents[file_path]['content'])
    else:
        print("File not found.")

def create_module_from_pydos_file(module_name, file_path):
    if file_path not in directory_contents:
        return None
    
    code = directory_contents[file_path]['content']
    module = types.ModuleType(module_name)
    module.__file__ = file_path
    module.__name__ = module_name
    
    try:
        exec(code, module.__dict__)
        return module
    except Exception as e:
        print(f"Error loading module {module_name}: {e}")
        return None

def run_command(args):
    if not args:
        print("Usage: run <filename.py>")
        return
    
    file_name = args
    file_path = f"{current_directory}/{file_name}".replace('//', '/')
    
    if file_path not in directory_contents:
        print(f"File '{file_name}' not found.")
        return
    
    if directory_contents[file_path]['type'] != 'exe':
        print(f"'{file_name}' is not an executable file.")
        return
    
    code = directory_contents[file_path]['content']
    
    exec_globals = {
        '__builtins__': __builtins__,
        '__name__': '__main__',
        '__file__': file_path,
    }
    
    temp_dir = tempfile.mkdtemp()
    original_path = sys.path.copy()
    sys.path.insert(0, temp_dir)
    
    try:
        for file_key in directory_contents:
            if directory_contents[file_key]['type'] == 'exe' and file_key.endswith('.py'):
                parts = file_key.strip('/').split('/')
                rel_path = '/'.join(parts)
                temp_file = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(temp_file), exist_ok=True)
                with open(temp_file, 'w') as f:
                    f.write(directory_contents[file_key]['content'])
        
        exec(code, exec_globals)
        
    except Exception as e:
        print(f"Error executing {file_name}: {e}")
    finally:
        sys.path = original_path
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def help_command(args=None):
    print("""

    =================================================
    [AVAILABLE COMMANDS:                            ]
    |  ---------- directory management -------------|
    |cd        - changes directory                  |
    |mkdir     - creates a directory                |
    |rmdir     - removes a directory                |
    |ls        - lists directory contents           |
    |  --------- file management -------------------|
    |mktf      - creates text files                 |
    |mkef      - creates executable files           |
    |rm        - removes files                      |
    |run       - runs executable files              |
    |vwtf      - shows file contents                |
    |copy      - copies files to another directory  |
    |move      - moves files to another directory   |
    |rem       - renames files                      |
    |edit      - edits existing files               |
    |   --------- system commands ------------------|
    |quit      - exits and saves                    |
    |sysinfo   - detailed system information        |
    |format    - resets filesystem                  |
    |clear     - clears terminal                    |
    |reboot    - reboots system                     |
    |  ---------- package manager ------------------|
    |install   -helps install pip packadges         |
    |uninstall -helps uninstall pip packages        |
    |  ---------- web based commands ---------------|
    |                                               |
    =================================================

    """)

def format_command():
    global kernel, current_directory, directory_contents
    try:
        kernel = {
            '/': {
                'type': 'directory',
                'contents': {
                    'bin': {'type': 'directory', 'contents': {}},
                    'usr': {'type': 'directory', 'contents': {}},
                    'tmp': {'type': 'directory', 'contents': {}}
                }
            }
        }
        current_directory = '/'
        directory_contents = {}
        
        try:
            readline.clear_history()
        except:
            pass
        
        save_filesystem()
        print("Filesystem formatted successfully.")
    except Exception as e:
        print(f"Error formatting: {e}")

def clear_command():
    clear_terminal()
    display_home()

def sysinfo_command():
    clear_terminal()
    print(PY_DOS)
    print("\n" + "="*70)
    print("SYSTEM INFORMATION".center(70))
    print("="*70 + "\n")
    
    print(f"Platform:          {platform.system()} {platform.release()}")
    print(f"Architecture:      {platform.machine()}")
    print(f"Processor:         {platform.processor()}")
    print(f"Python Version:    {sys.version.split()[0]}\n")
    
    print("-" * 70)
    print("HARDWARE RESOURCES")
    print("-" * 70 + "\n")
    
    cpu_percent, cpu_count = get_cpu_stats()
    print(f"CPU Cores:         {cpu_count}")
    print(f"CPU Usage:         {cpu_percent}%")
    
    mem_percent, mem_used, mem_total = get_memory_stats()
    print(f"\nMemory Usage:      {mem_percent}%")
    print(f"  Used:            {format_bytes(mem_used)}")
    print(f"  Total:           {format_bytes(mem_total)}")
    print(f"  Available:       {format_bytes(psutil.virtual_memory().available)}")
    
    disk_percent, disk_used, disk_total = get_disk_stats()
    print(f"\nDisk Usage:        {disk_percent}%")
    print(f"  Used:            {format_bytes(disk_used)}")
    print(f"  Total:           {format_bytes(disk_total)}")
    print(f"  Free:            {format_bytes(psutil.disk_usage('/').free)}")
    
    gpu_stats = get_gpu_stats()
    if gpu_stats:
        print(f"\nGPU Devices:       {len(gpu_stats)}")
        for idx, (name, gpu_load, gpu_mem_used, gpu_mem_total) in enumerate(gpu_stats):
            print(f"\n  GPU {idx}: {name}")
            print(f"    Load:         {gpu_load:.1f}%")
            print(f"    Memory Used:  {gpu_mem_used:.0f}MB / {gpu_mem_total:.0f}MB")
    else:
        print("\nGPU:               No GPU detected or GPUtil not installed")
    
    battery = psutil.sensors_battery()
    if battery:
        print(f"\nBattery:           {battery.percent}%")
        print(f"  Status:          {'Charging' if battery.power_plugged else 'Discharging'}")
        if battery.secsleft != psutil.POWER_TIME_UNKNOWN and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
            hours, remainder = divmod(battery.secsleft, 3600)
            minutes = remainder // 60
            print(f"  Time Remaining:  {hours}h {minutes}m")
    
    print("\n" + "-" * 70)
    print("FILESYSTEM")
    print("-" * 70 + "\n")
    print(f"Current Directory: {current_directory}")
    
    contents = kernel.get(current_directory, {}).get('contents', {})
    file_count = sum(1 for item in contents.values() if item['type'] == 'file')
    dir_count = sum(1 for item in contents.values() if item['type'] == 'directory')
    
    print(f"Files:             {file_count}")
    print(f"Directories:       {dir_count}")
    
    print("\n" + "="*70)

def quit_command():
    print("\nSaving filesystem...")
    bar_width = 40
    for i in range(bar_width + 1):
        progress = "#" * i + ":" * (bar_width - i)
        print(f"\r[{progress}]", end="", flush=True)
        time.sleep(0.05)
    print("\n")
    save_filesystem()
    sys.exit()

def reboot_command():
    save_filesystem()
    print("Rebooting...")
    time.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

command_functions = {
    'cd': cd_command,
    'mkdir': mkdir_command, 
    'md': mkdir_command,
    'rmdir': rmdir_command, 
    'rd': rmdir_command,
    'mktf': mktf_command, 
    'touch': mktf_command, 
    'copy con': mktf_command, 
    'echo': mktf_command,
    'vwtf': vwtf_command, 
    'cat': vwtf_command, 
    'type': vwtf_command,
    'mkef': mkef_command,
    'run': run_command, 
    'start': run_command, 
    'python': run_command,
    'rm': rm_command, 
    'del': rm_command,
    'copy': copy_command,
    'rem': rem_command,
    'move': move_command,
    'edit': edit_command,
    'install': install_command,
    'uninstall': uninstall_command,
}

no_args_command_functions = {
    'ls': ls_command, 
    'dir': ls_command,
    'help': help_command,
    'clear': clear_command, 
    'cls': clear_command,
    'sysinfo': sysinfo_command,
    'quit': quit_command,
    'format': format_command,
    'reboot': reboot_command,
}

def setup_readline():
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            history = save_data.get('command_history', [])
            
            for command in history:
                readline.add_history(command)
                
    except Exception as e:
        pass
    
    readline.set_history_length(10)

def save_history():
    history = []
    for i in range(readline.get_current_history_length()):
        history.append(readline.get_history_item(i + 1))
    
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
        else:
            save_data = {'kernel': kernel, 'current_directory': current_directory}
        
        save_data['command_history'] = history[-10:]
        
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
    except Exception as e:
        pass

def save_on_exit():
    save_history()
    try:
        save_data = {'kernel': kernel, 'current_directory': current_directory}
        history = []
        try:
            for i in range(readline.get_current_history_length()):
                history.append(readline.get_history_item(i + 1))
            save_data['command_history'] = history[-10:]
        except:
            save_data['command_history'] = []
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        save_file_contents()
    except:
        pass

atexit.register(save_on_exit)

def process_commands():
    user_input = check_input()
    command_parts = user_input.strip().split()
    
    if not command_parts:
        return
    
    command = command_parts[0].lower()
    args = ' '.join(command_parts[1:]) if len(command_parts) > 1 else None

    if command in command_functions:
        command_functions[command](args)
    elif command in no_args_command_functions:
        no_args_command_functions[command]()
    else:
        print(f"'{command}' is not recognized as an internal or external command")