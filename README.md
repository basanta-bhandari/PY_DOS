# PyDOS

A DOS-style terminal simulator built entirely in Python. Implements a virtual filesystem with file and directory management, a built-in package manager, system information display, and support for creating and running Python scripts from within the environment.

```
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
```

## Features

- Virtual filesystem with persistent state across sessions
- Create, edit, view, copy, move, and rename text and executable files
- Directory navigation and management
- Run Python scripts from within the virtual filesystem
- Live clock display in the terminal
- Battery status and real-time system info (CPU, memory, disk, GPU)
- Built-in pip package manager (`install` / `uninstall`)
- Command history (last 10 commands) saved and restored between sessions
- DOS-style aliases for common commands (`dir`, `cls`, `del`, `cat`, etc.)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip or pipx

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

### Directory Management

| Command | Alias | Description |
|---------|-------|-------------|
| `ls` | `dir` | List contents of the current directory |
| `cd <dir>` | | Change directory (`..` to go up, `/` for root) |
| `mkdir <dir>` | `md` | Create a new directory |
| `rmdir <dir>` | `rd` | Remove an empty directory |

### File Management

| Command | Description |
|---------|-------------|
| `mktf <filename>` | Create a text file (opens nvim / Notepad) |
| `mkef <filename>` | Create an executable Python file (opens nvim / Notepad) |
| `vwtf <filename>` | Print file contents to the terminal |
| `edit <filename>` | Edit an existing file |
| `rm <filename>` | Delete a file (`rm all` removes all files in the current directory) |
| `copy <file> to <dir>` | Copy a file to another directory |
| `move <file> to <dir>` | Move a file to another directory |
| `rem <file> to <newname>` | Rename a file |
| `run <filename>` | Execute a Python file from the virtual filesystem |

### System Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `sysinfo` | | Display CPU, memory, disk, GPU, and battery info |
| `clear` | `cls` | Clear the terminal and redraw the home screen |
| `reboot` | | Save state and restart PyDOS |
| `format` | | Reset the filesystem to its default state |
| `quit` | | Save state and exit |
| `help` | | Show the command reference |

### Package Manager

| Command | Description |
|---------|-------------|
| `install <package>` | Install a pip package |
| `uninstall <package>` | Uninstall a pip package |

## Editor

Text and executable files open in **nvim** on macOS/Linux and **Notepad** on Windows. When using nvim:

- `i` — enter insert mode
- `Esc` — exit insert mode
- `:wq` — save and exit
- `:q!` — exit without saving

## Project Structure

```
├── main.py                  # Entry point
├── utils.py                 # All commands and filesystem logic
├── pydos_filesystem.json    # Persisted filesystem state
├── saved/                   # Persisted file contents
├── requirements.txt
├── setup.py
└── README.md
```

## Troubleshooting

**`boot` command not found after installation:**
- Close and reopen your terminal
- Windows: ensure the Python Scripts directory is in your PATH
- macOS/Linux: ensure `~/.local/bin` is in your PATH
- Verify installation: `python -m pip show Py-DOS-B1`

**Permission errors on Linux/macOS:**
```bash
pip install --user Py-DOS-B1
```

**Made by Basanta Bhandari**