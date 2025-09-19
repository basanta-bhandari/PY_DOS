import time
import sys
import random
import os
import platform

virtual_fs = {
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
██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
██║        ██║       ██████╔╝╚██████╔╝███████║
╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
                                              
"""

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
    cd        ----->(changes the directory in which the user is situated; cd)
    mkdir     ----->(creates a directory; mkdir, md)
    rmdir     ----->(removes a directory; rmdir, rd)
    ls        ----->(lists contents in a directory; dir, ls)
    mktf      ----->(creates text files ; touch, copy con)
    
    """)

def cd_command(args):
    global current_directory
    if not args or len(args) < 2:
        print(current_directory)
        return
    
    target = args[1]
    if target == '..':
        if current_directory != '/':
            # Go up one level
            parts = current_directory.strip('/').split('/')
            if len(parts) > 1:
                current_directory = '/' + '/'.join(parts[:-1])
            else:
                current_directory = '/'
    else:
        # Go to subdirectory
        new_path = current_directory.rstrip('/') + '/' + target
        if new_path in virtual_fs or (current_directory in virtual_fs and target in virtual_fs[current_directory]['contents']):
            current_directory = new_path
        else:
            print("Directory not found")

# def mkdir_command(args):
    

def rmdir_command(args):
    if not args or len(args) < 2:
        print("Usage: rmdir <directory_name>")
        
    
    dirname = args[1]
    

def ls_command(args):
    if current_directory in virtual_fs:
        contents = virtual_fs[current_directory]['contents']
        if not contents:
            print("Directory is empty")
        else:
            for name, item in contents.items():
                if item['type'] == 'directory':
                    print(f"<DIR>    {name}")
                else:
                    print(f"         {name}")
    else:
        print("Current directory not found")

def mktf_command(args):
    if not args or len(args) < 2:
        print("Usage: mktf <filename>")
        return
    
    filename = args[1]


# Dictionary mapping commands to functions
command_functions = {
    'help': help_command,
    'cd': cd_command,
    'mkdir': mkdir_command,
    'rmdir': rmdir_command,
    'ls': ls_command,
    'mktf': mktf_command
}

def process_commands():
    user_input = check_input()
    command_parts = user_input.strip().split()
    
    if command_parts:
        command = command_parts[0].lower()
        
        if command in command_functions:
            command_functions[command](command_parts[1])
        else:
            print(f"'{command}' is not recognized as an internal or external command")
    # If empty input, just show prompt again
        
