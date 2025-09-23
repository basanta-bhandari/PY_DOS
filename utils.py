
import time
import sys
import random
import os
import platform
import json

FILE_CONTENT_FILE = 'pydos_file_contents.json'
file_contents = {}  # Will store all file contents organized
FILESYSTEM_FILE = 'pydos_filesystem.json'

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

PY_DOS="""
                            ██████╗ ██╗   ██╝    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
                                              
"""

def save_file_contents():
    """Save all file contents to JSON"""
    try:
        with open(FILE_CONTENT_FILE, 'w') as f:
            json.dump(file_contents, f, indent=2)
    except Exception as e:
        print(f"Error saving file contents: {e}")

def load_file_contents():
    """Load file contents from JSON"""
    global file_contents
    try:
        if os.path.exists(FILE_CONTENT_FILE):
            with open(FILE_CONTENT_FILE, 'r') as f:
                file_contents = json.load(f)
    except Exception as e:
        print(f"Error loading file contents: {e}")
        file_contents = {}

def save_filesystem():
    """Save the current filesystem state to JSON"""
    try:
        save_data = {
            'kernel': kernel,
            'current_directory': current_directory,
        }
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        save_file_contents()  # Save file contents separately
        print("State : NS [N/E]")
    except Exception as e:
        print(f"Error saving filesystem: {e}")

def load_filesystem():
    """Load filesystem state from JSON"""
    global kernel, current_directory
    
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            
            kernel = save_data.get('kernel', kernel)
            current_directory = save_data.get('current_directory', '/')
            load_file_contents()  # Load file contents separately
            print("Filesystem loaded from previous session.")
        else:
            print("State: CS [N/E]")
    except Exception as e:
        print(f"State: SS [E/E]  ----> CS")

def format_command():
    """Format the filesystem - reset to default state"""
    global kernel, current_directory, file_contents
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
        file_contents = {}  # Reset file contents too
        save_filesystem()
        print("Filesystem formatted successfully.")
    except Exception as e:
        print(f"Error formatting: {e}")

def clear_terminal():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

def get_current_path():
    return current_directory.replace('/', '\\') if current_directory != '/' else '\\'

def check_input():
    ipt = input(f"PY DOS {get_current_path()}> ")
    return ipt

def help_command(args=None):
    print("""
    AVAILABLE COMMANDS:
    cd        ----->(changes the directory in which the user is situated____; cd       )                [MF, .. , ./]
    mkdir     ----->(creates a directory____________________________________; mkdir,  md)               [MF--->main function]
    rmdir     ----->(removes a directory____________________________________; rmdir,  rd)               [MF ]
    ls        ----->(lists contents in a directory__________________________; dir,    ls)               [MF, dct, fls, .[extension] ]
    mktf      ----->(creates text files_____________________________________; echo,   touch, copy con)  [MF--->main function]
    mkef      ----->(creates exeutable files________________________________; [./], [.bat])             [MF--->main function]
    rm        ----->(removes files from )                                   ; del, em)                  [MF, all]
    run       ----->(runs executable program/code files_____________________; python,      start,)      [MF--->main function]
    vwtf      ----->(shows the contents of a text file______________________; cat,    type )            [MF--->main function]
    quit      ----->(exits the OS and saves changes made in system__________; ^C,      quit)            [MF--->main function]
    format    ----->(starts the OS on a clean slate_________________________; format     )              [MF--->main function]
    clear     ----->(clears the terminal____________________________________; clear,   cls)             [MF--->main function]
    """)



def normalize_path(path):
    """Normalize a path to handle .. and . properly"""
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

def cd_command(args):
    global current_directory
    if not args:
        print(current_directory)
        return
    
    target_path = normalize_path(args)
    
    # Check if the target directory exists
    if target_path in kernel and kernel[target_path]['type'] == 'directory':
        current_directory = target_path
    else:
        print("Current directory is non-accessable. " if current_directory == "/" else "Current directory not found.")

def mkdir_command(args):
    if not args:
        print("Usage: mkdir <directory_name>")
        return
        
    dirname = args
    new_path = normalize_path(dirname)
    
    # Check if directory already exists
    if new_path in kernel:
        print(f"Directory '{dirname}' already exists")
        return
    
    # Check if parent directory exists
    parent_path = '/'.join(new_path.split('/')[:-1]) or '/'
    if parent_path not in kernel:
        print("Parent directory not found")
        return
    
    # Create the directory
    kernel[new_path] = {'type': 'directory', 'contents': {}}
    
    # Add to parent's contents
    if parent_path in kernel:
        kernel[parent_path]['contents'][dirname] = {'type': 'directory', 'contents': {}}
    
    print(f"Directory '{dirname}' created")

def rmdir_command(args):
    if not args:
        print("Usage: rmdir <directory_name>")
        return
    
    dirname = args
    target_path = normalize_path(dirname)
    
    # Check if directory exists
    if target_path not in kernel:
        print("Directory not found")
        return
    
    # Check if it's a directory
    if kernel[target_path]['type'] != 'directory':
        print("Directory not found")
        return
    
    # Check if directory is empty
    if kernel[target_path]['contents']:
        print("Directory is not empty")
        return
    
    # Remove from kernel
    del kernel[target_path]
    
    # Remove from parent's contents
    parent_path = '/'.join(target_path.split('/')[:-1]) or '/'
    if parent_path in kernel:
        parent_name = target_path.split('/')[-1]
        if parent_name in kernel[parent_path]['contents']:
            del kernel[parent_path]['contents'][parent_name]

def ls_command():
    if current_directory in kernel:
        contents = kernel[current_directory]['contents']
        if not contents:
            print("Directory is empty")
        else:
            print(f"Directory of {current_directory} " if current_directory != "/" else "")
            print()
            for name, item in contents.items():
                if item['type'] == 'directory':
                    print(f"<DIR>          {name}")
                else:
                    print(f"<FILE>         {name}")
    else:
        print("Current directory not found.")


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
    
    # Store in organized file contents
    file_path = f"{current_directory}/{file_name}".replace('//', '/')
    file_contents[file_path] = {
        'type': 'txt',
        'content': content,
        'created_in': current_directory
    }
    
    # Add to kernel
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
    
    # Store in organized file contents
    file_path = f"{current_directory}/{file_name}".replace('//', '/')
    file_contents[file_path] = {
        'type': 'exe',
        'content': content,
        'created_in': current_directory
    }
    
    # Add to kernel
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
    
    print(f"Executable file '{file_name}' created successfully.")

def rm_command(args):
    if not args:
        print("Usage: rm <filename>")
        return
    
    file_path = f"{current_directory}/{args}".replace('//', '/')

    if file_path in file_contents:
        del file_contents[file_path]
        # Also remove from kernel
        if current_directory in kernel and args in kernel[current_directory]['contents']:
            del kernel[current_directory]['contents'][args]
        print(f"File '{args}' deleted.")

    elif args == 'all':
        current_directory =  cdr
        for i,z in cdr:
            if i in txt_files or i in exe_files:
                del kernel[current_directory]['contents'][i]
        print ("All files")
    else:
        print("File not found.")

def run_command(args):
    if not args:
        print("Usage: run <filename>")
        return
    
    file_path = f"{current_directory}/{args}".replace('//', '/')

    if file_path in file_contents and file_contents[file_path]['type'] == 'exe':
        try:
            code_to_execute = file_contents[file_path]['content']
            exec(code_to_execute)
        except Exception as e:
            print(f"Error executing {args}: {e}")
    else:
        print("File not found or not an executable file.")
    
    
def vwtf_command(args):
    if not args:
        print("Usage: vwtf <filename>")
        return
        
    file_name = args
    if file_name in txt_files:
        print(txt_files[file_name])
    else:
        print("File not found.")

# Dictionary mapping commands to functions
command_functions = {
    'cd': cd_command,
    'mkdir': mkdir_command,
    'md': mkdir_command,  # DOS alias
    'rmdir': rmdir_command,
    'rd': rmdir_command,  # DOS alias
    'mktf': mktf_command,
    'touch': mktf_command,  # Unix alias
    'copy con' : mktf_command,
    'vwtf': vwtf_command,
    'echo': mktf_command,  # Basic alias
    'cat': vwtf_command,   # Unix alias
    'type' :vwtf_command,
    'mkef': mkef_command,
    'start': run_command,
    'python' : run_command,
    'run' : run_command,
    'rm'  : rm_command,
    'del' : rm_command
}

def clear_command():
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version 1.2] ")
    print("Enter help for instruction menu. \n")

def quit_command():
    save_filesystem()
    print("Filesystem saved. Goodbye!")
    sys.exit()

no_args_command_functions = {
    'ls': ls_command,
    'dir': ls_command,  # DOS alias
    'help': help_command,
    'clear': clear_command,
    'cls': clear_command,  # DOS alias
    'quit': quit_command,
    'format': format_command,
}


def process_commands():
    user_input = check_input()
    command_parts = user_input.strip().split()
    
    if not command_parts:
        return  # Empty input, just return
    
    command = command_parts[0].lower()
    args = ' '.join(command_parts[1:]) if len(command_parts) > 1 else None
    
    if command in command_functions:
        command_functions[command](args)
    elif command in no_args_command_functions:
        no_args_command_functions[command]()
    else:
        print(f"'{command}' is not recognized as an internal or external command")



