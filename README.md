# PyDOS

A nostalgic DOS-like operating system simulator that runs in your terminal! Experience the classic command-line interface with familiar DOS commands.

## Features

- **Classic DOS Commands**: cd, mkdir, rmdir, ls/dir, and more
- **File System**: Create and navigate directories with persistent storage
- **Text File Support**: Create and view text files
- **Authentic Experience**: DOS-style prompts and interface
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

Install PyDOS using pipx (recommended):

```bash
pipx install pydos
```

Or using pip:

```bash
pip install pydos
```

## Usage

Simply run:

```bash
pydos
```

## Available Commands

- `cd` - Change directory
- `mkdir` / `md` - Create directory  
- `rmdir` / `rd` - Remove directory
- `ls` / `dir` - List directory contents
- `mktf` / `touch` - Create text files
- `vwtf` / `cat` - View text file contents
- `clear` / `cls` - Clear screen
- `format` - Reset filesystem
- `quit` - Exit PyDOS
- `help` - Show help menu

## Example Session

```
PY DOS \> mkdir projects
Directory 'projects' created

PY DOS \> cd projects
PY DOS \projects> mktf hello.txt
Write your text for 'hello.txt' and type '\s' on a new line to save.
Hello, PyDOS world!
\s
File 'hello.txt' created successfully.

PY DOS \projects> ls
         hello.txt

PY DOS \projects> vwtf hello.txt
Hello, PyDOS world!
```

## Author

Created by Basanta Bhandari

Relive the classic computing experience with PyDOS! 🖥️