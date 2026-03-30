```
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
```

A DOS-style terminal simulator built entirely in Python. Implements a virtual filesystem with file and directory management, a built-in package manager, system information display, and support for creating and running Python scripts from within the environment.

## Features

- Virtual filesystem with persistent state across sessions
- Create, edit, view, copy, move, and rename text and executable files
- Directory navigation and management
- Run Python scripts from within the virtual filesystem
- Live clock display in the terminal
- Battery status and file 'encryption inside simulator
- Built-in pip package manager (`install` / `uninstall`)
- Command history (last 10 commands) saved and restored between sessions

## To be added:
- Web browsing features( with a network connectivity interface)
- lock screen/security
- manipulation/veiwing of actual device settings (storage, CPU/GPU usage, etc)


## Installation

### Prerequisites

- Python 3.7 or higher
- pip/pipx

### Installing pipx (recommended)

**Windows:**
```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```
Restart your terminal after running these.

**macOS:**
```bash
brew install pipx
```
Or without Homebrew:
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install pipx
```

**Linux (other distros):**
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

### Installing PyDOS

**Using pipx (recommended):**
```bash
pipx install Py-DOS-B1
```

**Using pip:**
```bash
pip install Py-DOS-B1
```

**Running locally:**
```bash
git clone https://github.com/basanta-bhandari/PY_DOS
cd PY_DOS
pip install -r requirements.txt
python main.py
```

On some systems a virtual environment is required first:
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Running PyDOS

```bash
boot
```

## Commands

# Directory,file & system commands can be viewed through the 'help' command.

### Package Manager

 `install <package>`-------->Installs a pip package 
 `uninstall <package>`------>Uninstalls a pip package 

## Editor
Text and executable files open in **nvim** on macOS/Linux and **Notepad** on Windows. When using nvim:
- `i` -> enter insert mode
- `Esc` -> exit insert mode
- `:wq` -> save and exit
- `:q!` -> exit without saving

## Troubleshooting
- Close and reopen your terminal
- Windows: ensure the Python Scripts directory is in your PATH
- macOS/Linux: ensure `~/.local/bin` is in your PATH
- Verify installation: `python -m pip show Py-DOS-B1`

**Permission errors on Linux/macOS:**
```bash
pip install --user Py-DOS-B1
```
