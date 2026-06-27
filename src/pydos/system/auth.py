import os, sys, pickle, hashlib
import readchar
from ..fs.kernel import state
from ..fs.persistence import AUTH_FILE, ensure_saved_folder

PASS_SLOTS = 8

def _hash(raw): return hashlib.sha256(raw.encode()).hexdigest()

def _load_auth():
    try:
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception:
        pass
    return None

def _save_auth(data):
    ensure_saved_folder()
    with open(AUTH_FILE, 'wb') as f:
        pickle.dump(data, f)

def _delete_auth():
    try:
        if os.path.exists(AUTH_FILE):
            os.remove(AUTH_FILE)
    except Exception:
        pass

def read_password_masked(prompt):
    sys.stdout.write(prompt); sys.stdout.flush()
    entered = []
    while True:
        ch = readchar.readchar()
        if ch in ('\r', '\n'):
            print(); break
        elif ch in ('\x7f', '\x08'):
            if entered:
                entered.pop()
                clear = ' ' * (len(prompt) + PASS_SLOTS + 2)
                sys.stdout.write(f"\r{clear}\r{prompt}{'*' * len(entered)}")
                sys.stdout.flush()
        elif len(entered) < PASS_SLOTS:
            entered.append(ch)
            sys.stdout.write('*'); sys.stdout.flush()
    return ''.join(entered)

def _lockscreen_prompt(message=None):
    from ..display import clear_terminal, PY_DOS
    clear_terminal()
    print(PY_DOS)
    if message:
        print(f"{'Incorrect password!':^80}\n")
    pad   = ' ' * 30
    blank = '_' * PASS_SLOTS
    sys.stdout.write(f"{pad}Password [{blank}]"); sys.stdout.flush()
    entered = []
    while True:
        ch = readchar.readchar()
        if ch in ('\r', '\n'):
            break
        elif ch in ('\x7f', '\x08'):
            if entered:
                entered.pop()
                display = '*' * len(entered) + '_' * (PASS_SLOTS - len(entered))
                sys.stdout.write(f"\r{pad}Password [{display}]"); sys.stdout.flush()
        elif len(entered) < PASS_SLOTS:
            entered.append(ch)
            display = '*' * len(entered) + '_' * (PASS_SLOTS - len(entered))
            sys.stdout.write(f"\r{pad}Password [{display}]"); sys.stdout.flush()
    print()
    return ''.join(entered)

def display_lockscreen():
    auth = _load_auth()
    if not auth or not auth.get('hash'):
        return
    message = None
    while True:
        raw = _lockscreen_prompt(message=message)
        if _hash(raw) == auth['hash']:
            return
        message = True

def pass_command(args):
    if not args:
        print("Usage:\n  pass set\n  pass change\n  pass rm"); return
    sub = args.split()[0].lower()
    if sub == 'set':
        if _load_auth():
            print("Password already set. Use 'pass change'."); return
        raw = read_password_masked("New password (max 8 chars): ")
        if not raw:
            print("Password cannot be empty."); return
        if read_password_masked("Confirm: ") != raw:
            print("Mismatch. Not set."); return
        _save_auth({'hash': _hash(raw)}); print("Password set.")
    elif sub == 'change':
        auth = _load_auth()
        if not auth:
            print("No password set. Use 'pass set'."); return
        if _hash(read_password_masked("Current: ")) != auth['hash']:
            print("Incorrect."); return
        new = read_password_masked("New password: ")
        if not new:
            print("Cannot be empty."); return
        if read_password_masked("Confirm: ") != new:
            print("Mismatch. Not changed."); return
        _save_auth({'hash': _hash(new)}); print("Password changed.")
    elif sub == 'rm':
        auth = _load_auth()
        if not auth:
            print("No password set."); return
        if _hash(read_password_masked("Current password: ")) != auth['hash']:
            print("Incorrect. Aborted."); return
        if input("Remove password? [y/N]: ").strip().lower() == 'y':
            _delete_auth(); print("Password removed.")
        else:
            print("Aborted.")
    else:
        print(f"Unknown: '{sub}'. Use set / change / rm")
