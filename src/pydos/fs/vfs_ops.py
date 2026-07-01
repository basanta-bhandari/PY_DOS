import os, sys, shutil, fnmatch, shlex, tempfile
from .kernel import kernel, directory_contents, state, normalize_path, join_path, get_dir_node
from .persistence import save_filesystem, save_file_contents

def cd_command(args):
    if not args:
        print(state.current_directory); return
    if args == '..':
        if state.current_directory == '/': return
        parts = state.current_directory.rstrip('/').split('/')
        state.current_directory = '/'.join(parts[:-1]) or '/'
        return
    if args == '/':
        state.current_directory = '/'; return
    target = args if args.startswith('/') else (
        (state.current_directory.rstrip('/') + '/' + args) if state.current_directory != '/' else '/' + args
    )
    target = target.rstrip('/') or '/'
    parts = target.strip('/').split('/') if target != '/' else []
    node = kernel['/']
    for part in parts:
        if 'contents' in node and part in node['contents'] and node['contents'][part]['type'] == 'directory':
            node = node['contents'][part]
        else:
            print(f"Directory not found: {args}"); return
    state.current_directory = target
    save_filesystem()

def mkdir_command(args):
    if not args:
        print("Usage: mkdir <dirname>"); return
    new_path = normalize_path(args)
    if new_path in kernel:
        print(f"Directory '{args}' already exists"); return
    parent_path = '/'.join(new_path.split('/')[:-1]) or '/'
    parent_node = get_dir_node(parent_path)
    if parent_node is None:
        print("Parent directory not found."); return
    name = new_path.split('/')[-1]
    new_node = {'type': 'directory', 'contents': {}}
    kernel[new_path] = new_node
    parent_node['contents'][name] = new_node
    save_filesystem()
    print(f"Directory '{args}' created")

def rmdir_command(args):
    if not args:
        print("Usage: rmdir <dirname>"); return
    target = normalize_path(args)
    if target not in kernel or kernel[target]['type'] != 'directory':
        print("Directory not found"); return
    if kernel[target]['contents']:
        print("Directory is not empty"); return
    del kernel[target]
    parent = '/'.join(target.split('/')[:-1]) or '/'
    if parent in kernel:
        kernel[parent]['contents'].pop(target.split('/')[-1], None)
    save_filesystem()

def ls_command(args=None):
    long_fmt = show_hidden = False
    pattern = None
    if args:
        try:
            tokens = shlex.split(args)
        except ValueError:
            tokens = args.split()
        for tok in tokens:
            if tok.startswith('-'):
                if 'l' in tok: long_fmt = True
                if 'a' in tok: show_hidden = True
            else:
                pattern = tok
    node = get_dir_node()
    if node is None:
        print("Current directory not found."); return 1
    contents = node.get('contents', {})
    names = [n for n in contents if show_hidden or not n.startswith('.')]
    if pattern:
        names = [n for n in names if fnmatch.fnmatch(n, pattern)]
        if not names:
            print(f"ls: no match: {pattern}"); return 1
    if not names:
        print("Directory is empty"); return 0
    if state.current_directory != '/':
        print(f"Directory of {state.current_directory}\n")
    for name in sorted(names):
        item = contents[name]
        if long_fmt:
            fpath = join_path(state.current_directory, name)
            ftype = 'DIR ' if item['type'] == 'directory' else 'FILE'
            size_str = f"{len(directory_contents.get(fpath, {}).get('content', '')):>8} B" if fpath in directory_contents else '       -  '
            print(f"{ftype}  {size_str}  {name}")
        else:
            tag = '<DIR>' if item['type'] == 'directory' else '<FILE>'
            print(f"{tag}          {name}")
    return 0

def grep_command(args):
    if not args:
        print("Usage: grep <pattern> [file]"); return 1
    try:
        tokens = shlex.split(args)
    except ValueError:
        tokens = args.split()
    flags   = [t for t in tokens if t.startswith('-')]
    rest    = [t for t in tokens if not t.startswith('-')]
    if not rest:
        print("grep: missing pattern"); return 1
    pattern     = rest[0]
    ignore_case = '-i' in flags
    invert      = '-v' in flags
    filename    = rest[1] if len(rest) > 1 else None
    if filename:
        fpath = join_path(state.current_directory, filename)
        if fpath not in directory_contents:
            print(f"grep: {filename}: No such file"); return 1
        text = directory_contents[fpath].get('content', '')
    elif state.piped_input is not None:
        text = state.piped_input
    else:
        print("grep: no input"); return 1
    found = False
    for line in text.splitlines():
        hay = line.lower() if ignore_case else line
        pat = pattern.lower() if ignore_case else pattern
        if fnmatch.fnmatch(hay, f'*{pat}*') != invert:
            print(line); found = True
    return 0 if found else 1

def _open_editor(temp_path):
    state.editor_open = True
    editor = os.environ.get('VISUAL') or os.environ.get('EDITOR') or (
        'notepad' if sys.platform.startswith('win') else 'nvim'
    )
    os.system(f"{editor} {temp_path}")
    state.editor_open = False

def mkfile_command(args):
    """Create a text file (formerly mktf)."""
    if not args:
        print("Usage: mkfile <filename>"); return
    fpath = join_path(state.current_directory, args)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        tmp = f.name
    print("\nCreating text file...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save | ':q!' to discard")
    input("Press ENTER to continue...")
    _open_editor(tmp)
    with open(tmp) as f:
        content = f.read()
    directory_contents[fpath] = {'type': 'txt', 'content': content, 'created_in': state.current_directory}
    if state.current_directory in kernel:
        kernel[state.current_directory]['contents'][args] = {'type': 'file'}
    os.unlink(tmp)
    save_file_contents(); save_filesystem()
    print(f"Text file '{args}' created.")

def mkexe_command(args):
    """Create an executable file (formerly mkef)."""
    if not args:
        print("Usage: mkexe <filename>"); return
    fpath = join_path(state.current_directory, args)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        tmp = f.name
    print("\nCreating executable file...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save | ':q!' to discard")
    input("Press ENTER to continue...")
    _open_editor(tmp)
    with open(tmp) as f:
        content = f.read()
    directory_contents[fpath] = {'type': 'exe', 'content': content, 'created_in': state.current_directory}
    if state.current_directory in kernel:
        kernel[state.current_directory]['contents'][args] = {'type': 'file'}
    os.unlink(tmp)
    save_file_contents(); save_filesystem()
    print(f"Executable file '{args}' created.")

def edit_command(args):
    if not args:
        print("Usage: edit <filename>"); return
    fpath = join_path(state.current_directory, args)
    if fpath not in directory_contents:
        print("File not found."); return
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(directory_contents[fpath]['content'])
        tmp = f.name
    print("\nOpening editor...")
    input("Press ENTER to continue...")
    _open_editor(tmp)
    with open(tmp) as f:
        directory_contents[fpath]['content'] = f.read()
    os.unlink(tmp)
    save_file_contents(); save_filesystem()
    print(f"Saved '{args}'")

def show_command(args):
    """View file contents (formerly vwtf)."""
    if not args:
        print("Usage: show <filename>"); return
    fpath = join_path(state.current_directory, args)
    if fpath in directory_contents:
        print(directory_contents[fpath]['content'])
    else:
        print("File not found.")

def rm_command_ex(args, recursive=False, force=False, interactive=False, dry_run=False):
    if not args:
        if not force: print("Usage: rm [-r] [-f] <name>")
        return
    target = join_path(state.current_directory, args)
    if target in directory_contents:
        if dry_run: print(f"would remove '{args}'"); return
        if interactive and input(f"Remove '{args}'? [y/N]: ").strip().lower() != 'y': return
        del directory_contents[target]
        kernel.get(state.current_directory, {}).get('contents', {}).pop(args, None)
        save_file_contents(); save_filesystem()
        print(f"File '{args}' deleted.")
        return
    if recursive and target in kernel and kernel[target]['type'] == 'directory':
        def _rm(path):
            for name, item in list(kernel[path]['contents'].items()):
                cp = join_path(path, name)
                if item['type'] == 'directory': _rm(cp)
                else: directory_contents.pop(cp, None)
            del kernel[path]
        parent = '/'.join(target.split('/')[:-1]) or '/'
        _rm(target)
        kernel.get(parent, {}).get('contents', {}).pop(target.split('/')[-1], None)
        save_file_contents(); save_filesystem()
        print(f"Directory '{args}' removed.")
        return
    if not force:
        print(f"'{args}' is a directory. Use rm -r to remove it." if target in kernel else "File not found.")

def rm_command(args):
    rm_command_ex(args)

def copy_command(args):
    if not args or ' to ' not in args:
        print("Usage: copy <file> to <dir>"); return
    src_name, tgt_path = [x.strip() for x in args.split(' to ', 1)]
    src = join_path(state.current_directory, src_name)
    if src not in directory_contents:
        print("Source file not found"); return
    tgt_path = normalize_path(tgt_path)
    if tgt_path not in kernel:
        print("Target directory not found"); return
    tgt = join_path(tgt_path, src_name)
    directory_contents[tgt] = {**directory_contents[src], 'created_in': tgt_path}
    kernel[tgt_path]['contents'][src_name] = {'type': 'file'}
    save_file_contents(); save_filesystem()
    print(f"'{src_name}' copied to {tgt_path}.")

def move_command(args):
    if not args or ' to ' not in args:
        print("Usage: move <file> to <dir>"); return
    src_name, tgt_path = [x.strip() for x in args.split(' to ', 1)]
    src = join_path(state.current_directory, src_name)
    if src not in directory_contents:
        print("Source file not found"); return
    tgt_path = normalize_path(tgt_path)
    if tgt_path not in kernel:
        print("Target directory not found"); return
    tgt = join_path(tgt_path, src_name)
    directory_contents[tgt] = {**directory_contents[src], 'created_in': tgt_path}
    del directory_contents[src]
    kernel[state.current_directory]['contents'].pop(src_name, None)
    kernel[tgt_path]['contents'][src_name] = {'type': 'file'}
    save_file_contents(); save_filesystem()
    print(f"'{src_name}' moved to {tgt_path}.")

def rem_command(args):
    if not args or ' to ' not in args:
        print("Usage: rem <name> to <newname>"); return
    old, new = [x.strip() for x in args.split(' to ', 1)]
    old_path = join_path(state.current_directory, old)
    new_path = join_path(state.current_directory, new)
    if old_path not in directory_contents:
        print("File not found."); return
    if new_path in directory_contents:
        print("File already exists."); return
    directory_contents[new_path] = directory_contents.pop(old_path)
    kernel[state.current_directory]['contents'].pop(old, None)
    kernel[state.current_directory]['contents'][new] = {'type': 'file'}
    save_file_contents(); save_filesystem()
    print(f"'{old}' renamed to '{new}'.")

