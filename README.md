```
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
```

A DOS-style terminal simulator built entirely in Python. Implements a virtual filesystem with file and directory management, a built-in package manager, system information display, and support for creating and running Python scripts from within the environment.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

## Features

- Virtual filesystem with persistent state across sessions
- Create, edit, view, copy, move, and rename text and executable files
- Directory navigation and management (`cd`, `cd ..`, `/`)
- Run Python scripts from within the virtual filesystem
- Live clock display in the terminal
- Battery status and file encryption inside simulator
- Built-in pip package manager (`install` / `uninstall`)
- Command history (last 10 commands) saved and restored between sessions
- **Command pipelining** with pipe operators (`|`)
- **Conditional execution** with `&&` operator (run next command only if previous succeeds)
- **Output redirection** (`>`, `>>`, `2>`, `2>&1`, `&>`)
- **Input redirection** (`<`)
- **Variable expansion** with `$VAR` and `${VAR}` syntax
- **Exit code support** via `$?` special variable
- **Glob pattern expansion** (`*`, `?`, `[...]`)
- **Echo command** for printing text with variable substitution
- **Help system** with detailed command documentation

## Built-in Applications

### Lantern 
A peer-to-peer mesh chat application for PyDOS.
- Host or join mesh chat rooms
- Yggdrasil IPv6 mesh network support
- Real-time messaging with other PyDOS instances
- Commands: `run setup` for mesh network setup, `run community` to host or join chat

### Lynx
A text-based web browser integrated into PyDOS.
- Browse URLs directly from the terminal
- Automatic lynx installation with OS detection (apt, pacman, dnf, brew, zypper)
- Fallback manual installation instructions for unsupported systems
- Cross-platform support: Windows, macOS, Linux
- Commands: `run web [url]` to launch

### RubOS (Rubus Engine)
A BASIC-inspired CLI language for creating custom applications within PyDOS.

**Features:**
- Variables and arrays: `let x = 5`, `let arr = [1, 2, 3]`
- Input/output: `println`, `ask`, `read_file`, `write_file`
- Control flow: `if/elif/else`, `while`, `loop`, `for`
- Functions: `def greet(name) ... return ... end`
- List operations: `append arr "item"`, `menu ["Yes", "No"]`
- File operations: `read_file "file.txt"`, `write_file "out.txt" content`
- Utilities: `clear`, `pause`, `color`, `exit`, `list_dir`
- Comments with `#`

**Creating Custom Apps:**
- `create -cli <appname>` - Create a new RubOS application
- Edit the generated `main.rub` file
- Run the app by typing its name
- Check app status with `state <appname>`

**Example:**
```bash
create -cli mygame
cd /home/user/apps/mygame
edit main.rub
mygame
```



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
PYTHONPATH=src python -m pydos
```

On some systems a virtual environment is required first:
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=src python -m pydos
```

**OS-Specific Package Manager Detection:**
When running Lynx, PyDOS automatically detects your system's package manager and attempts to install it:
- **Linux**: apt, apt-get (Debian/Ubuntu), pacman (Arch), dnf (Fedora/RHEL), zypper (openSUSE), apk (Alpine)
- **macOS**: brew (Homebrew)
- **Windows**: Provides manual installation instructions
- **Fallback**: Detailed manual installation instructions if automatic detection fails

### Running PyDOS

```bash
boot
```

## Commands

All directory, file & system commands can be viewed through the 'help' command.

### Package Manager

`install <package>` ------> Installs a Python package via pip  
`uninstall <package>` ---> Uninstalls a Python package via pip  
`packages` -----------> Lists all installed packages 

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

---

**Status**: Beta (v1.2)  
Enjoy your retro experience! Feel like a Boomer! 
