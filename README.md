# PyDOS

A work-in-progress DOS simulator for the terminal. This is an early version that implements basic DOS-style commands and filesystem operations. Still figuring out the best way to handle some features, but it's functional enough to play around with.

```
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
```

## Installation

### Prerequisites
- Python 3.7 or higher (check with `python3 --version` or `python --version`)
- pip (comes with Python) or pipx

### Installing pipx (recommended method)

**Windows:**
```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```
Restart your command prompt after installation.

**macOS:**
```bash
brew install pipx
```
Or if you don't have Homebrew:
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install pipx
```

**Linux (other distributions):**
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

### Installing PyDOS

**Method 1: Using pipx (recommended)**
```bash
pipx install Py-DOS-B1
```

**Method 2: Using pip**
```bash
pip install Py-DOS-B1
```

On some systems you may need to use `pip3`:
```bash
pip3 install Py-DOS-B1
```

### Running PyDOS
```bash
boot
```

### Troubleshooting

**Command not found after installation:**
- Close and reopen your terminal
- On Windows: Make sure Python Scripts directory is in your PATH
- On macOS/Linux: Make sure `~/.local/bin` is in your PATH
- Try running: `python -m pip show Py-DOS-B1` to verify installation

**Permission errors on Linux/macOS:**
Add `--user` flag to pip install:
```bash
pip install --user Py-DOS-B1
```