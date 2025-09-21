
import time
import sys
import random
import os
import platform
import json


FILESYSTEM_FILE = 'pydos_filesystem.json'

txt_files = {

}

exec_files ={

}

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

def save_filesystem():
    """Save the current filesystem state to JSON"""
    try:
        save_data = {
            'kernel': kernel,
            'current_directory': current_directory,
            'txt_files': txt_files
        }
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        print("State : NS [N/E]")
    except Exception as e:
        print(f"Error saving filesystem: {e}")

def load_filesystem():
    """Load filesystem state from JSON, or use default if file doesn't exist"""
    global kernel, current_directory, txt_files
    
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            
            kernel = save_data.get('kernel', kernel)
            current_directory = save_data.get('current_directory', '/')
            txt_files = save_data.get('txt_files', {})
            print("Filesystem loaded from previous session.")
        else:
            print("State: CS [N/E]")
    except Exception as e:
        print(f"State: SS [E/E]  ----> CS")

def format_command():
    """Format the filesystem - reset to default state"""
    global kernel, current_directory, txt_files
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
        txt_files = {}
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
    cd        ----->(changes the directory in which the user is situated____; cd       )
    mkdir     ----->(creates a directory____________________________________; mkdir, md)
    rmdir     ----->(removes a directory____________________________________; rmdir, rd)
    ls        ----->(lists contents in a directory__________________________; dir,   ls)
    mktf      ----->(creates text files_____________________________________; touch, copy con)
    mkef      ----->(creates executable files_______________________________; [             ]) 
    run       ----->(runs executable program/code files_____________________; [         ])
    vwtf      ----->(shows the contents of a text file______________________; echo,   cat)
    quit      ----->(exits the OS and saves changes made in system__________; ^C,     quit)
    format    ----->(starts the OS on a clean slate_________________________; format     )
    clear     ----->(clears the terminal____________________________________; clear,  cls)

    NOTE : [CD] [all cd commands work]
         : [MKEF, RUN][please don't use main, utils or setup.py; THIS INCONVINIENCE I SOON TO BE FIXED.]
         : [THE COMMANDS WHICH HAVE NO FUNCTION AND/OR ALTERNATIVE LISTING ARE SOON TO BE FIXED.]
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
        print("Directory not found")

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
            print(f"Directory of {current_directory}")
            print()
            for name, item in contents.items():
                if item['type'] == 'directory':
                    print(f"<DIR>          {name}")
                else:
                    print(f"<FILE>         {name}")
    else:
        print("Current directory not found")


def mktf_command(args):
    global txt_files
    if not args:
        print("Usage: mktf <filename>")
        return
    
    file_name = args
    input_list = []
    print(f"Write your text for '{file_name}' and type '\s' on a new line to save.")
    
    while True:
        try:
            line = input()
            if line.strip() == '\s':
                break
            input_list.append(line)
        except EOFError:
            break
        except Exception as e:
            print(f"An unexpected error occurred during input: {e}")
            return
    
    content_of_txtfile = "\n".join(input_list)
    txt_files[file_name] = content_of_txtfile
    
    # Add file to current directory in kernel
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file', 'content': content_of_txtfile}
    
    try:
        with open(file_name, "w") as file:
            file.write(content_of_txtfile)
        print(f"File '{file_name}' created and content written successfully.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


def mkef_command(args):
    global exec_files
    if not args:
        print("Usage: mkef <filename>")
        return
    
    file_name = args
    input_list = []
    print(f"Write your code for '{file_name}' and type '\s' on a new line to save.")
    
    while True:
        try:
            line = input()
            if line.strip() == '\s':
                break
            input_list.append(line)
        except EOFError:
            break
        except Exception as e:
            print(f"An unexpected error occurred during input: {e}")
            return
    
    content_of_execfile = "\n".join(input_list)
    exec_files[file_name] = content_of_execfile
    
    # Add file to current directory in kernel
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file', 'content': content_of_execfile}
    
    try:
        with open(file_name, "w") as file:
            file.write(content_of_execfile)
        print(f"File '{file_name}' created and code written successfully.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}") 


def run_command(args):
    file_name = args
    if not args:
        print("Usage: run <filename>")
        return
    if file_name in exec_files:
        with open(file_name, "r") as f:
            code_to_execute = f.read()
        exec(code_to_execute)
    else:
        print("File not found.")

    
    
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
    'vwtf': vwtf_command,
    'echo': vwtf_command,  # Basic alias
    'cat': vwtf_command,   # Unix alias
    'mkef': mkef_command,
    'run' : run_command
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



