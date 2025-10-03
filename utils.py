import time
import sys
import random
import os
import platform
import json
import readline
import atexit
import pickle
from pathlib import Path

FILESYSTEM_FILE = 'pydos_filesystem.json'
SAVED_FOLDER = 'saved'  # All files stored here in binary

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
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
"""

# UTILITY FUNCTIONS
def clear_terminal():
    os.system('cls' if sys.platform.startswith('win') else 'clear')

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
    """Safely join paths handling root directory"""
    if base == '/':
        return '/' + name
    return base + '/' + name

def ensure_saved_folder():
    """Ensure the saved folder exists"""
    Path(SAVED_FOLDER).mkdir(exist_ok=True)

# FILE SYSTEM PERSISTENCE WITH BINARY STORAGE
def save_file_contents():
    """Save all file contents to binary format in 'saved' folder"""
    try:
        ensure_saved_folder()
        file_path = Path(SAVED_FOLDER) / 'file_contents.bin'
        with open(file_path, 'wb') as f:
            pickle.dump(directory_contents, f)
    except Exception as e:
        print(f"Error saving file contents: {e}")

def load_file_contents():
    """Load file contents from binary storage"""
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
        
        # Add current command history (last 10 only)
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

# DIRECTORY COMMANDS
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

# FILE COMMANDS
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

    if file_path in directory_contents:
        contents = directory_contents[file_path]['content']  
        print(f"Edit your content for '{file_name}' and type '\\s' on a new line to save.")
        print("Current content:")
        print(contents)
        print("--- Continue editing below ---")
        
        input_list = []
        contents_list = contents.split('\n')
        input_list += contents_list
        
        while True:
            try: 
                line = input()
                if line.strip() == '\\s':
                    break
                input_list.append(line)
            except EOFError:
                break
                
        content = "\n".join(input_list)
        directory_contents[file_path] = {
            'type': directory_contents[file_path]['type'],
            'content': content,
            'created_in': current_directory
        }
        if current_directory in kernel:
            kernel[current_directory]['contents'][file_name] = {'type': 'file'}
        save_file_contents()
        save_filesystem()
        print(f"New content saved on '{file_name}' successfully.")
    else:
        print("File not found.")

def vwtf_command(args):
    if not args:
        print("Usage: vwtf <filename>")
        return
        
    file_path = join_path(current_directory, args)
    if file_path in directory_contents:
        print(directory_contents[file_path]['content'])
    else:
        print("File not found.")
         
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
    
    import re
    
    # Find all imports
    from_imports = re.findall(r'from\s+(\S+)\s+import', code)
    direct_imports = re.findall(r'^import\s+(\S+)', code, re.MULTILINE)
    
    all_imports = set(from_imports + direct_imports)
    
    # Load PyDOS modules first
    for module_name in all_imports:
        module_file = f"{current_directory}/{module_name}.py".replace('//', '/')
        
        if module_file in directory_contents:
            module_code = directory_contents[module_file]['content']
            try:
                exec(module_code, exec_globals)
            except Exception as e:
                print(f"Error loading module {module_name}: {e}")
                return
    
    # Remove import statements for PyDOS modules from the code
    for module_name in all_imports:
        module_file = f"{current_directory}/{module_name}.py".replace('//', '/')
        if module_file in directory_contents:
            # Remove "from module import *" statements
            code = re.sub(rf'from\s+{module_name}\s+import\s+\*\s*\n?', '', code)
            # Remove "from module import x, y, z" statements
            code = re.sub(rf'from\s+{module_name}\s+import\s+[^\n]+\n?', '', code)
            # Remove "import module" statements
            code = re.sub(rf'^import\s+{module_name}\s*\n?', '', code, flags=re.MULTILINE)
    
    # Execute the main code
    try:
        exec(code, exec_globals)
    except Exception as e:
        print(f"Error executing {file_name}: {e}")

# SYSTEM COMMANDS
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
    print(PY_DOS)
    print("PY DOS [Version Beta]")
    print("Enter help for instruction menu.\n")

def quit_command():
    save_filesystem()
    print("Filesystem saved. Goodbye!")
    sys.exit()

# COMMAND PROCESSING
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