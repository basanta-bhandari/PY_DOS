import os, sys, shutil, subprocess, tempfile, types, time
from importlib import resources
from ..fs.kernel import kernel, directory_contents, state, join_path, normalize_path
from ..fs.persistence import save_filesystem, save_file_contents, FILESYSTEM_FILE, SAVED_FOLDER

# ── RubOS ─────────────────────────────────────────────────────────────────────

_rubus_module = None

def _get_rubus():
    global _rubus_module
    if _rubus_module: return _rubus_module
    try:
        from pydos.appdata import rubus_engine
        _rubus_module = rubus_engine
    except ImportError:
        pass
    return _rubus_module

USER_APPS_DIR = '/Apps/User'
_APP_TEMPLATE = '''# My PY_DOS App — RubOS
println "Hello from my app!"
ask "Press Enter to continue..." -> _
'''

def _ensure_user_apps_dir():
    root = kernel['/']['contents']
    if 'Apps' not in root:
        root['Apps'] = {'type': 'directory', 'contents': {}}
    apps = root['Apps']['contents']
    if 'User' not in apps:
        node = {'type': 'directory', 'contents': {}}
        apps['User'] = node
        kernel[USER_APPS_DIR] = node
    elif USER_APPS_DIR not in kernel:
        kernel[USER_APPS_DIR] = apps['User']

def _list_user_apps():
    _ensure_user_apps_dir()
    return list(kernel[USER_APPS_DIR].get('contents', {}).keys())

def _get_app_source(name):
    return directory_contents.get(f"{USER_APPS_DIR}/{name}/main.rub", {}).get('content')

def create_command(args):
    if not args or not args.startswith('-cli '):
        print("Usage: create -cli <appname>"); return 1
    name = args[5:].strip().lower().replace(' ', '_')
    if not name.isidentifier():
        print(f"Invalid app name '{name}'."); return 1
    _ensure_user_apps_dir()
    if name in kernel[USER_APPS_DIR]['contents']:
        print(f"App '{name}' already exists."); return 1
    app_dir  = f"{USER_APPS_DIR}/{name}"
    node     = {'type': 'directory', 'contents': {'main.rub': {'type': 'file'}}}
    kernel[USER_APPS_DIR]['contents'][name] = node
    kernel[app_dir] = node
    directory_contents[f"{app_dir}/main.rub"] = {'type': 'txt', 'content': _APP_TEMPLATE, 'created_in': app_dir}
    save_file_contents(); save_filesystem()
    print(f"Created '{name}' at {app_dir}/main.rub")
    print(f"  Edit : cd {app_dir} && edit main.rub")
    print(f"  Check: state {name}  |  Run: {name}")
    return 0

def state_command(args):
    if not args:
        apps = _list_user_apps()
        if not apps: print("No user apps. Use 'create -cli <name>'.")
        else:
            print("User apps:")
            for a in apps:
                print(f"  {a:<20} {'OK' if _get_app_source(a) else 'missing main.rub'}")
        return 0
    src = _get_app_source(args.strip())
    if src is None:
        print(f"App '{args.strip()}' not found."); return 1
    rubus = _get_rubus()
    if rubus is None:
        print("[!] RubOS engine not available."); return 1
    errors = rubus.check(src)
    if not errors:
        print(f"[{args.strip()}] OK — {src.count(chr(10))+1} lines, no errors.")
    else:
        print(f"[{args.strip()}] {len(errors)} error(s):"); [print(e) for e in errors]
    return 0 if not errors else 1

def _run_user_app(name):
    src = _get_app_source(name)
    if src is None: return None
    rubus = _get_rubus()
    if rubus is None: return None
    ctx = rubus.PYDOSContext(
        directory_contents, kernel, state.current_directory,
        join_path, save_file_contents, save_filesystem
    )
    return rubus.run(src, ctx)

# ── App seeding ───────────────────────────────────────────────────────────────

def seed_apps():
    _ensure_user_apps_dir()
    _seed_lynx(); _seed_mutiny()

def _seed_lynx():
    LYNX_DIR  = '/Apps/Utilities/Lynx'
    LYNX_FILE = f'{LYNX_DIR}/web'
    _ensure_path(LYNX_DIR)
    if LYNX_FILE not in directory_contents:
        try:
            code = resources.files("pydos.appdata").joinpath("lynx.py").read_text(encoding="utf-8")
            directory_contents[LYNX_FILE] = {'type':'exe','content':code,'created_in':LYNX_DIR}
            kernel[LYNX_DIR]['contents']['web'] = {'type':'file'}
        except Exception as e:
            print(f"[Core] Lynx seed failed: {e}")

def _seed_mutiny():
    MUTINY_DIR   = '/Apps/Utilities/Mutiny'
    _ensure_path(MUTINY_DIR)
    try:
        pkg = resources.files("pydos.appdata.mutiny")
        for fname in ('setup.py', 'community.py'):
            fpath = f"{MUTINY_DIR}/{fname.replace('.py','')}"
            if fpath not in directory_contents:
                code = pkg.joinpath(fname).read_text(encoding="utf-8")
                directory_contents[fpath] = {'type':'exe','content':code,'created_in':MUTINY_DIR}
                kernel[MUTINY_DIR]['contents'][fname.replace('.py','')] = {'type':'file'}
    except Exception as e:
        print(f"[Core] Mutiny seed failed: {e}")

def _ensure_path(path):
    parts = path.strip('/').split('/')
    node  = kernel['/']
    current = ''
    for part in parts:
        current = f"/{part}" if not current else f"{current}/{part}"
        if part not in node['contents']:
            new = {'type':'directory','contents':{}}
            node['contents'][part] = new
            kernel[current] = new
        node = node['contents'][part]
        if current not in kernel:
            kernel[current] = node

# ── run ───────────────────────────────────────────────────────────────────────

def run_command(args):
    if not args:
        print("Usage: run <filename> [args]"); return
    parts     = args.split(None, 1)
    file_name = parts[0]
    run_args  = parts[1] if len(parts) > 1 else ''
    file_path = join_path(state.current_directory, file_name).replace('//', '/')
    if file_path not in directory_contents:
        for alt in (f"/Apps/Utilities/Mutiny/{file_name}", f"/Apps/Utilities/Lynx/{file_name}"):
            if alt in directory_contents:
                file_path = alt; break
        else:
            print(f"File '{file_name}' not found."); return
    if directory_contents[file_path]['type'] != 'exe':
        print(f"'{file_name}' is not executable."); return
    code = directory_contents[file_path]['content']
    exec_globals = {'__builtins__': __builtins__, '__name__': '__main__',
                    '__file__': file_path, '_pydos_run_args_': run_args}
    tmp = tempfile.mkdtemp()
    orig = sys.path.copy(); sys.path.insert(0, tmp)
    try:
        exec(code, exec_globals)
    except Exception as e:
        print(f"Error executing {file_name}: {e}")
    finally:
        sys.path = orig
        shutil.rmtree(tmp, ignore_errors=True)

# ── install / packages ────────────────────────────────────────────────────────

def install_command(args):
    if not args:
        print("Usage: install <package>"); return
    pkg = args.strip()
    print(f"\n[*] Installing '{pkg}' via pip...")
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[✓] Installed '{pkg}'.")
    else:
        print(f"[✗] Failed: {result.stderr.strip()}")

def uninstall_command(args):
    if not args:
        print("Usage: uninstall <package>"); return
    result = subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', args.strip()],
                            capture_output=True, text=True)
    print(f"[✓] Uninstalled." if result.returncode == 0 else f"[✗] {result.stdout or result.stderr}")

def packages_command(args=None):
    print("\n[*] Installed packages:\n")
    result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=columns'],
                            capture_output=True, text=True)
    print(result.stdout if result.returncode == 0 else "[!] Could not retrieve package list.")

# ── misc ──────────────────────────────────────────────────────────────────────

def echo_command(args):
    if not args:
        print(); return 0
    text = args.strip().strip('"').strip("'")
    for k, v in state.shell_vars.items():
        text = text.replace(f'${k}', v)
    text = text.replace('$?', str(state.last_exit))
    print(text); return 0

def help_command(args=None):
    print("""
    =================================================
    [AVAILABLE COMMANDS                             ]
    |--------- directory management ----------------|
    |cd        - change directory                   |
    |mkdir     - create directory                   |
    |rmdir     - remove empty directory             |
    |ls        - list directory contents            |
    |--------- file management ---------------------|
    |mktf      - create text file                   |
    |mkef      - create executable file             |
    |rm        - remove file/directory              |
    |run       - run executable                     |
    |vwtf      - view file contents                 |
    |copy      - copy file to directory             |
    |move      - move file to directory             |
    |rem       - rename file                        |
    |edit      - edit existing file                 |
    |grep      - search file contents               |
    |--------- system commands ---------------------|
    |quit      - save and exit                      |
    |sysinfo   - system information                 |
    |format    - reset filesystem                   |
    |clear     - clear terminal                     |
    |reboot    - reboot PY DOS                      |
    |--------- package manager ---------------------|
    |install   - install pip package                |
    |uninstall - uninstall pip package              |
    |packages  - list installed packages            |
    |--------- security ----------------------------|
    |pass set  - set boot password                  |
    |pass change - change password                  |
    |pass rm   - remove password                    |
    |--------- apps --------------------------------|
    |run web [url]  - launch Lynx browser           |
    |run setup      - Yggdrasil mesh setup          |
    |run community  - host or join mesh chat        |
    |create -cli <name> - scaffold RubOS app        |
    |state <name>       - check RubOS app           |
    |pkgs / packages    - list pip packages         |
    =================================================
    """)

def clear_command():
    from ..display import clear_terminal, display_home
    clear_terminal(); display_home()

def format_command():
    from ..fs.kernel import reset_kernel
    from ..display import clear_terminal
    reset_kernel()
    try:
        import readline; readline.clear_history()
    except Exception: pass
    if os.path.exists(FILESYSTEM_FILE):
        os.remove(FILESYSTEM_FILE)
    if os.path.exists(SAVED_FOLDER):
        shutil.rmtree(SAVED_FOLDER)
    pkg_root = os.path.dirname(os.path.abspath(__file__))
    for dirpath, dirnames, _ in os.walk(pkg_root):
        for d in dirnames:
            if d == '__pycache__':
                shutil.rmtree(os.path.join(dirpath, d))
    print("Filesystem formatted and cache cleared.")

def quit_command():
    print("\nSaving...")
    bar = 40
    for i in range(bar + 1):
        print(f"\r[{'#'*i + ':'*(bar-i)}]", end="", flush=True)
        time.sleep(0.03)
    print()
    save_filesystem()
    sys.exit()

def reboot_command():
    save_filesystem()
    print("Rebooting...")
    time.sleep(1)
    os.execv(sys.executable, [sys.executable, '-m', 'pydos'] + sys.argv[1:])
