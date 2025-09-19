import time
import sys
import random
import os
import platform
import json


FILESYSTEM_FILE = 'pydos_filesystem.json'

txt_files = {

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
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
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
            'current_directory': current_directory
        }
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        print ("State : NS [N/E]")
    except Exception as e:
        print(f"Error saving filesystem: {e}")

def load_filesystem():
    """Load filesystem state from JSON, or use default if file doesn't exist"""
    global kernel, current_directory
    
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            
            kernel = save_data.get('kernel', kernel)
            current_directory = save_data.get('current_directory', '/')
            print("Filesystem loaded from previous session.")
        else:
            print("State: CS [N/E]")
    except Exception as e:
        print(f"State: SS [E/E]  ----> CS")

def format_command():
    try:
        save_data = {
            'kernel': kernel,
            'current_directory': current_directory
        }
        with open(FILESYSTEM_FILE, 'w') as f:
            data = json.load(f)
            data = None
    except Exception as e:
        print(f"Error formatting: {e}")
    save_filesystem()

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
    vwtf      ----->(shows the contents of a text file______________________; echo,   cat)
    quit      ----->(exits the OS and saves changes made in system__________; ^C,     quit)
    format    ----->(starts the OS on a clean slate_________________________; format     )
    clear     ----->(clears the terminal____________________________________; clear,  cls)
    
    """)

def cd_command(args):
    global current_directory
    if not args or len(args) < 2:
        print(current_directory)
        return
    
    target = args
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
        if new_path in kernel or (current_directory in kernel and target in kernel[current_directory]['contents']):
            current_directory = new_path
        else:
            print("Directory not found")

def mkdir_command(args):
    dirname = args
    if not args or len(args) < 2:
        print("Usage: mkdir <directory_name>")
    if current_directory in kernel:
        kernel[current_directory]['contents'][dirname] = {'type': 'directory', 'contents': {}}
        kernel[current_directory.rstrip('/') + '/' + dirname] = {'type': 'directory', 'contents': {}}
        print(f"Directory '{dirname}' created")
    else:
        print("Current directory not found")


def rmdir_command(args):
    if not args or len(args) < 2:
        print("Usage: rmdir <directory_name>")
    dirname = args
    if current_directory in kernel:
        contents = kernel[current_directory]['contents']
        if dirname in contents:
            contents.pop(dirname)
        if not contents:
            print("Directory is empty")
        
    

def ls_command():
    if current_directory in kernel:
        contents = kernel[current_directory]['contents']
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
    global txt_files
    # Ensure correct number of arguments
    if len(args) < 1:
        print("Usage: mktf <filename>")
        return
    file_name = args
    input_list = []
    print(f"Write your text for '{file_name}' and type '\\s' on a new line to save.")
    while True:
        try:
            line = input()
            # Check if the user has entered the save command on a new line
            if line.strip() == '\\s':
                break
            input_list.append(line)
        except EOFError:
            # Handle Ctrl+D (Unix) or Ctrl+Z (Windows) if the user ends the input stream
            break
        except Exception as e:
            print(f"An unexpected error occurred during input: {e}")
            return
    # Combine the list of lines into a single string with newlines
    content_of_txtfile = "\n".join(input_list)
    txt_files[file_name] = content_of_txtfile
    try:
        # Open the file in write mode ('w') and write the content
        with open(file_name, "w") as file:
            file.write(content)
        print(f"File '{file_name}' created and content written successfully.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


def vwtf_command(args):
    file_name= args
    if not args or len(args) < 2:
        print("Usage: rmdir <directory_name>")
    if file_name in txt_files:
        print(txt_files[file_name])
    else:
        print("File not found.")

# Dictionary mapping commands to functions
command_functions = {
    'cd': cd_command,
    'mkdir': mkdir_command,
    'rmdir': rmdir_command,
    'mktf': mktf_command
}

def clear_command():
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version 1.2] ")
    print("Enter help for instruction menu. \n")
    load_filesystem()
    while True:
        try:
            process_commands()
        except KeyboardInterrupt:
            print("\n")
            break

def quit_command():
    save_filesystem()
    sys.exit()

no_args_command_functions ={
    'ls': ls_command,
    'help': help_command,
    'clear': clear_command,
    'quit' : quit_command,
    'format' : format_command,
}



def process_commands():
    user_input = check_input()
    command_parts = user_input.strip().split()
    
    if command_parts:
        command = command_parts[0].lower()
        
        if command in command_functions:
            command_functions[command](command_parts[1])
        elif command in no_args_command_functions :
            no_args_command_functions[command]()
        else:
            print(f"'{command}' is not recognized as an internal or external command")
    

    # If empty input, just show prompt again
        
