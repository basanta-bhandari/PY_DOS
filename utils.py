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
clock_running = False
clock_thread = None

directory_contents = {}
current_directory = '/'
kernel = {
    '/': {
        'type': 'directory',
        'contents': {
            'bin': {'type': 'directory', 'contents': {}},
            'usr': {'type': 'directory', 'contents': {}},
            'tmp': {'type': 'directory', 'contents': {}},
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

def update_time_display():
    global clock_running
    
    while clock_running:
        current_time = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\033[s")
        sys.stdout.write(f"\033[12;1H")
        sys.stdout.write(f"Time: [{current_time}]" + " " * 20)
        sys.stdout.write(f"\033[u")
        sys.stdout.flush()
        time.sleep(1)

def start_clock():
    global clock_running, clock_thread
    clock_running = True
    clock_thread = threading.Thread(target=update_time_display, daemon=True)
    clock_thread.start()

def stop_clock():
    global clock_running
    clock_running = False

    
def clear_terminal():
    os.system('cls' if sys.platform.startswith('win') else 'clear')

def display_home():
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version Alpha]")
    print("ENTER 'help' TO GET STARTED.")
    print("="*32)
    get_battery_status()
    update_time_display()
    start_clock()
    

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

        

def cd_command(args):
    global current_directory
    if not args:
        print(current_directory)
        return
    
    target_path = normalize_path(args)
    if target_path in kernel and kernel[target_path]['type'] == 'directory':
        current_directory = target_path
    else:
        print("Directory not found.")

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
    if parent_path not in kernel:
        print("Parent directory not found")
        return
    
    dir_name_only = new_path.split('/')[-1]
    kernel[new_path] = {'type': 'directory', 'contents': {}}
    kernel[parent_path]['contents'][dir_name_only] = {'type': 'directory', 'contents': {}}
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
    if current_directory not in kernel:
        print("Current directory not found.")
        return
    
    contents = kernel[current_directory]['contents']
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
    input_list = []
    print(f"Write your text for '{file_name}' and type '\\s' on a new line to save.")
    
    while True:
        try:
            line = input()
            if line.strip() == '\\s':
                break
            input_list.append(line)
        except EOFError:
            break
    
    content = "\n".join(input_list)
    file_path = join_path(current_directory, file_name)
    directory_contents[file_path] = {
        'type': 'txt',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()
    print(f"Text file '{file_name}' created successfully.")

def mkef_command(args):
    if not args:
        print("Usage: mkef <filename>")
        return
    
    file_name = args
    input_list = []
    print(f"Write your code for '{file_name}' and type '\\s' on a new line to save.")
    
    while True:
        try:
            line = input()
            if line.strip() == '\\s':
                break
            input_list.append(line)
        except EOFError:
            break
    
    content = "\n".join(input_list)
    file_path = join_path(current_directory, file_name)
    directory_contents[file_path] = {
        'type': 'exe',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
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
    file_name = args
    file_path = join_path(current_directory, args)

    if file_path not in directory_contents:
        print("File not found.")
        return
        
    contents = directory_contents[file_path]['content']
    lines = contents.split('\n')
    current_line = 0
    
    print(f"Editing '{file_name}'. Commands: Ctrl+S (save), Ctrl+Q (quit), Ctrl+D (delete line)")
    print("Arrow keys: UP/DOWN to navigate lines, ENTER to edit current line")
    
    def display_lines():
        clear_terminal()
        print(f"=== Editing: {file_name} ===\n")
        for i, line in enumerate(lines):
            prefix = ">" if i == current_line else " "
            print(f"{prefix} {i + 1}: {line}")
        print(f"\n[Line {current_line + 1}/{len(lines)}] Ctrl+S=Save | Ctrl+Q=Quit | Ctrl+D=Delete")
    
    display_lines()
    
    while True:
        try:
            key = readchar.readkey()
            
            if key == readchar.key.UP and current_line > 0:
                current_line -= 1
                display_lines()
            elif key == readchar.key.DOWN and current_line < len(lines) - 1:
                current_line += 1
                display_lines()
            elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                print(f"\n\nEditing line {current_line + 1}:")
                readline.set_startup_hook(lambda: readline.insert_text(lines[current_line]))
                try:
                    new_content = input("")
                    lines[current_line] = new_content
                finally:
                    readline.set_startup_hook()
                display_lines()
            elif key == '\x13':
                content = "\n".join(lines)
                directory_contents[file_path]['content'] = content
                save_file_contents()
                save_filesystem()
                print(f"\nSaved '{file_name}'")
                time.sleep(1)
                display_lines()
            elif key == '\x11':
                break
            elif key == '\x04':
                if 0 <= current_line < len(lines):
                    del lines[current_line]
                    if current_line >= len(lines) and lines:
                        current_line = len(lines) - 1
                    display_lines()
                        
        except KeyboardInterrupt:
            break
        
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
            if directory_contents[file_key]['type'] == 'exe':
                if file_key.startswith(current_directory):
                    rel_path = file_key[len(current_directory):].lstrip('/')
                    if rel_path.endswith('.py'):
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
    AVAILABLE COMMANDS:
    cd        - changes directory
    mkdir     - creates a directory
    rmdir     - removes a directory
    ls        - lists directory contents
    mktf      - creates text files
    mkef      - creates executable files
    rm        - removes files
    run       - runs executable files
    vwtf      - shows file contents
    copy      - copies files to another directory
    move      - moves files to another directory
    rem       - renames files
    edit      - edits existing files
    quit      - exits and saves
    format    - resets filesystem
    clear     - clears terminal
    reeboot   - reboots system
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
    stop_clock()
    clear_terminal()
    display_home()
    

def quit_command():
    stop_clock()
    save_filesystem()
    print("Filesystem saved. Goodbye!")
    sys.exit()

def reboot_command():
    stop_clock()
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
    'edit': edit_command
}

no_args_command_functions = {
    'ls': ls_command, 
    'dir': ls_command,
    'help': help_command,
    'clear': clear_command, 
    'cls': clear_command,
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