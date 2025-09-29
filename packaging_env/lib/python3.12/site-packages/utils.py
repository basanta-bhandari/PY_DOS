import time
import sys
import random
import os
import platform
import json
import readline
import atexit

FILE_CONTENT_FILE = 'pydos_file_contents.json'
FILESYSTEM_FILE = 'pydos_filesystem.json'


directory_contents = {}
current_directory = '/'
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

# FILE SYSTEM PERSISTENCE
def save_file_contents():
    try:
        with open(FILE_CONTENT_FILE, 'w') as f:
            json.dump(directory_contents, f, indent=2)
    except Exception as e:
        print(f"Error saving file contents: {e}")

def load_file_contents():
    global directory_contents
    try:
        if os.path.exists(FILE_CONTENT_FILE):
            with open(FILE_CONTENT_FILE, 'r') as f:
                directory_contents = json.load(f)
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
            save_data['command_history'] = history[-10:]  # Keep only last 10
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
    
    kernel[new_path] = {'type': 'directory', 'contents': {}}
    if parent_path in kernel:
        kernel[parent_path]['contents'][dirname] = {'type': 'directory', 'contents': {}}
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
        parent_name = target_path.split('/')[-1]
        if parent_name in kernel[parent_path]['contents']:
            del kernel[parent_path]['contents'][parent_name]


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
    if not args or "to" not in args:
        print("Usage: rem <originalname> to <newname>")
        return
    
    parts = args.split("to")
    file_name = parts[0].strip()
    new_file_name = parts[1].strip()
    
    file_path = f"{current_directory}/{file_name}".replace('//', '/')
    new_file_path = f"{current_directory}/{new_file_name}".replace('//', '/')

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
    file_path = f"{current_directory}/{file_name}".replace('//', '/')
    directory_contents[file_path] = {
        'type': 'txt',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
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
    file_path = f"{current_directory}/{file_name}".replace('//', '/')
    directory_contents[file_path] = {
        'type': 'exe',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
    print(f"Executable file '{file_name}' created successfully.")

def rm_command(args):
    if not args:
        print("Usage: rm <filename>")
        return
    
    if args == 'all':
        if current_directory in kernel:
            files_to_remove = [name for name, item in kernel[current_directory]['contents'].items() if item['type'] == 'file']
            for file_name in files_to_remove:
                file_path = f"{current_directory}/{file_name}".replace('//', '/')
                if file_path in directory_contents:
                    del directory_contents[file_path]
                del kernel[current_directory]['contents'][file_name]
            print("All files removed")
        return
    
    file_path = f"{current_directory}/{args}".replace('//', '/')
    if file_path in directory_contents:
        del directory_contents[file_path]
        if current_directory in kernel and args in kernel[current_directory]['contents']:
            del kernel[current_directory]['contents'][args]
        print(f"File '{args}' deleted.")
    else:
        print("File not found.")

def copy_command(args):    
    if not args or ' to ' not in args:
        print("Usage: copy <filename> to <directory>")
        return
    
    parts = args.split('to')
    file_name = parts[0].strip()
    target_path = parts[1].strip()
    source_path = f"{current_directory}/{file_name}".replace('//', '/')

    if source_path not in directory_contents:
        print("Source file not found")
        return

    if target_path not in kernel:
        print("Target directory not found")
        return

    content = directory_contents[source_path]
    target_file_path = f"{target_path}/{file_name}".replace('//', '/')
    directory_contents[target_file_path] = {
        'type': directory_contents[source_path]['type'],
        'content': content['content'],
        'created_in': target_path
    }
    
    kernel[target_path]['contents'][file_name] = {'type': 'file'}
    print(f"File '{file_name}' copied to {target_path} successfully.")

def move_command(args):
    if not args or ' to ' not in args:
        print("Usage: move <filename> to <directory>")
        return
    
    parts = args.split('to')
    file_name = parts[0].strip()
    target_path = parts[1].strip()
    source_path = f"{current_directory}/{file_name}".replace('//', '/')

    if source_path not in directory_contents:
        print("Source file not found")
        return

    if target_path not in kernel:
        print("Target directory not found")
        return

    content = directory_contents[source_path]  
    target_file_path = f"{target_path}/{file_name}".replace('//', '/')  
    
    directory_contents[target_file_path] = {
        'type': directory_contents[source_path]['type'],
        'content': content['content'],
        'created_in': target_path
    }
    del directory_contents[source_path]
    del kernel[current_directory]['contents'][file_name]
    kernel[target_path]['contents'][file_name] = {'type': 'file'}
    print(f"File '{file_name}' moved to {target_path} successfully.")

def  edit_command(args):
    if not args:
        print("Usage: edit <filename>")
        return
    file_name = args
    file_path = f"{current_directory}/{args}".replace('//', '/')

    if file_path in directory_contents:
        contents = directory_contents[file_path]['content']  
        print(f"""Edit your content for '{file_name}' and type '\\s' on a new line to save.
                {contents}""")
        while True:
            input_list = []
            contents_list = contents.split('\n')
            input_list += contents_list
            try: 
                line = input()
                if line.strip() == '\\s':
                    break
                input_list.append(line)
            except EOFError:
                break
        content = "\n".join(input_list)
        directory_contents[file_path] = {
            'type': 'exe',
            'content': content,
            'created_in': current_directory
        }
        if current_directory in kernel:
            kernel[current_directory]['contents'][file_name] = {'type': 'file'}
        print(f"New content saved on '{file_name}' successfully.")
    else:
        print("File not found.")

def vwtf_command(args):
    if not args:
        print("Usage: vwtf <filename>")
        return
        
    file_path = f"{current_directory}/{args}".replace('//', '/')
    if file_path in directory_contents:
        print(directory_contents[file_path]['content'])
    else:
        print("File not found.")

    if file_path in directory_contents:
        directory_contents[new_file_path] = directory_contents[file_path]
        del directory_contents[file_path]
        del kernel[current_directory]['contents'][file_name]  
        kernel[current_directory]['contents'][new_file_name] = {'type': 'file'}
        print(f"'{file_name}' renamed to '{new_file_name}' successfully.")    

    
         
def run_command(args):
    if not args:
        print("Usage: run <filename>")
        return
    
    file_path = f"{current_directory}/{args}".replace('//', '/')
    if file_path in directory_contents and directory_contents[file_path]['type'] == 'exe':
        try:
            code_to_execute = directory_contents[file_path]['content']
            exec(code_to_execute)
        except Exception as e:
            print(f"Error executing {args}: {e}")
    else:
        print("File not found or not an executable file.")

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
    quit      - exits and saves
    format    - resets filesystem
    clear     - clears terminal
    rem       - renames files
    move      - moves files
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
        save_filesystem()
        print("Filesystem formatted successfully.")
    except Exception as e:
        print(f"Error formatting: {e}")

def clear_command():
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version 1.4]")
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
    'rem' : rem_command,
    'move' : move_command,
    'edit' : edit_command
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
    # Load history from your existing filesystem data
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            history = save_data.get('command_history', [])
            
            # Load each command into readline history
            for command in history:
                readline.add_history(command)
                
    except Exception as e:
        pass  # If loading fails, start with empty history
    
    readline.set_history_length(10)  # Changed to 10

def save_history():
    # Get current history from readline
    history = []
    for i in range(readline.get_current_history_length()):
        history.append(readline.get_history_item(i + 1))
    
    # Save it with your existing filesystem data
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
        else:
            save_data = {'kernel': kernel, 'current_directory': current_directory}
        
        save_data['command_history'] = history[-10:]  # Keep last 10 commands only
        
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
    except Exception as e:
        pass  # If saving fails, don't crash
atexit.register(save_history)

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

# Structure :

# Imports and global variables
# Utility functions
# File system persistence functions
# Directory operations
# File operations
# System commands
# Command processing

