import os, json, pickle, atexit
from pathlib import Path
from .kernel import kernel, directory_contents, state, reconcile_kernel_flat_index

FILESYSTEM_FILE = 'pydos_filesystem.json'
SAVED_FOLDER    = 'saved'
AUTH_FILE       = f'{SAVED_FOLDER}/pydos_auth.bin'
_LEGACY_BIN     = f'{SAVED_FOLDER}/file_contents.bin'

def ensure_saved_folder():
    Path(SAVED_FOLDER).mkdir(exist_ok=True)

# ── file contents ────────────────────────────────────────────────────────────

def save_file_contents():
    try:
        ensure_saved_folder()
        with open(Path(SAVED_FOLDER) / 'file_contents.json', 'w') as f:
            json.dump(directory_contents, f)
    except Exception as e:
        print(f"Error saving file contents: {e}")

def load_file_contents():
    global directory_contents
    # migrate legacy pickle
    legacy = Path(_LEGACY_BIN)
    if legacy.exists():
        try:
            with open(legacy, 'rb') as f:
                data = pickle.load(f)
            directory_contents.update(data)
            legacy.unlink()
            save_file_contents()
            print("[FS] Migrated file contents from legacy format.")
            return
        except Exception:
            pass
    try:
        p = Path(SAVED_FOLDER) / 'file_contents.json'
        if p.exists():
            with open(p) as f:
                directory_contents.update(json.load(f))
    except Exception as e:
        print(f"Error loading file contents: {e}")

# ── filesystem ───────────────────────────────────────────────────────────────

def save_filesystem():
    try:
        data = {
            'kernel':            kernel,
            'current_directory': state.current_directory,
            'sys_profile':       state.sys_profile,
        }
        try:
            import readline
            data['command_history'] = [
                readline.get_history_item(i + 1)
                for i in range(readline.get_current_history_length())
            ][-10:]
        except Exception:
            data['command_history'] = []
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        save_file_contents()
        print("State : NS [N/E]")
    except Exception as e:
        print(f"Error saving filesystem: {e}")

def load_filesystem():
    if os.path.exists(FILESYSTEM_FILE):
        try:
            with open(FILESYSTEM_FILE) as f:
                data = json.load(f)
            kernel.clear()
            kernel.update(data.get('kernel', {}))
            state.current_directory = data.get('current_directory', '/')
            state.sys_profile       = data.get('sys_profile', {})
            load_file_contents()
            print("Filesystem loaded from previous session.")
        except Exception:
            print("State: SS [E/E]  ----> CS")
    else:
        print("State: CS [N/E]")
    reconcile_kernel_flat_index()

# ── history ──────────────────────────────────────────────────────────────────

def setup_readline():
    try:
        import readline
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE) as f:
                data = json.load(f)
            for cmd in data.get('command_history', []):
                readline.add_history(cmd)
        readline.set_history_length(10)
    except Exception:
        pass

def save_on_exit():
    try:
        data = {}
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE) as f:
                data = json.load(f)
        data['kernel']            = kernel
        data['current_directory'] = state.current_directory
        try:
            import readline
            data['command_history'] = [
                readline.get_history_item(i + 1)
                for i in range(readline.get_current_history_length())
            ][-10:]
        except Exception:
            data['command_history'] = []
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        save_file_contents()
    except Exception:
        pass

atexit.register(save_on_exit)
