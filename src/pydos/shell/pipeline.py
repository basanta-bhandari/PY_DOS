import sys, shlex, contextlib, io, subprocess
from ..fs.kernel import kernel, directory_contents, state, join_path, get_dir_node
from ..fs.persistence import save_file_contents, save_filesystem
import fnmatch

_REDIRECT_OPS = ('2>&1', '&>', '>>', '2>', '>', '<')

def _expand_vars(s):
    s = s.replace('~', '/')
    s = s.replace('$?', str(state.last_exit))
    for k, v in state.shell_vars.items():
        s = s.replace(f'${k}', v).replace(f'${{{k}}}', v)
    return s

def _glob_match(names, pattern):
    return [n for n in names if fnmatch.fnmatch(n, pattern)]

def _expand_globs(args_str):
    if not args_str: return args_str
    try: tokens = shlex.split(args_str)
    except ValueError: tokens = args_str.split()
    node  = get_dir_node()
    names = list(node['contents'].keys()) if node else []
    result = []
    for tok in tokens:
        if any(c in tok for c in ('*','?','[')):
            matched = _glob_match(names, tok)
            result.extend(matched if matched else [tok])
        else:
            result.append(tok)
    return ' '.join(shlex.quote(t) if ' ' in t else t for t in result)

def _write_vfile(name, content, append=False):
    fpath = join_path(state.current_directory, name)
    if append and fpath in directory_contents:
        content = directory_contents[fpath].get('content', '') + content
    directory_contents[fpath] = {'type':'txt','content':content,'created_in':state.current_directory}
    kernel[state.current_directory]['contents'][name] = {'type':'file'}
    save_file_contents(); save_filesystem()

def _read_vfile(name):
    fpath = join_path(state.current_directory, name)
    return directory_contents[fpath].get('content','') if fpath in directory_contents else None

def _parse_redirects(cmd_str):
    redirects = []; remaining = cmd_str
    for op in _REDIRECT_OPS:
        while op in remaining:
            idx    = remaining.find(op)
            before = remaining[:idx]
            after  = remaining[idx+len(op):].lstrip()
            if op == '2>&1':
                redirects.append((op, None)); remaining = before + after; break
            parts = after.split(None, 1)
            if not parts: break
            redirects.append((op, parts[0]))
            remaining = before + (parts[1] if len(parts) > 1 else '')
            break
    return remaining.strip(), redirects

def _split_on_op(s, op):
    parts=[]; current=[]; in_sq=in_dq=False; i=0
    while i < len(s):
        c = s[i]
        if c=="'" and not in_dq: in_sq = not in_sq
        elif c=='"' and not in_sq: in_dq = not in_dq
        if not in_sq and not in_dq and s[i:i+len(op)]==op:
            parts.append(''.join(current)); current=[]; i+=len(op); continue
        current.append(c); i+=1
    parts.append(''.join(current))
    return parts

def _strip_flags(args, flags):
    if not args: return args, set()
    parts = args.split(); found = set(); remaining = []
    for p in parts:
        if p in flags: found.add(p)
        else: remaining.append(p)
    return ' '.join(remaining) or None, found

def _dispatch_single(raw_cmd, stdin_data=None):
    from ..fs.vfs_ops import (cd_command, mkdir_command, rmdir_command, ls_command,
                               grep_command, mkfile_command, mkexe_command, edit_command,
                               show_command, rm_command, rm_command_ex, copy_command,
                               move_command, rem_command)
    from ..shell.builtins import (run_command, install_command, uninstall_command,
                                   packages_command, echo_command, help_command,
                                   clear_command, format_command, quit_command,
                                   reboot_command, create_command, state_command,
                                   _run_user_app)
    from ..system.auth import pass_command
    from ..system.sysinfo import sysinfo_command

    state.piped_input = stdin_data
    raw_cmd = raw_cmd.strip()
    if not raw_cmd or raw_cmd.startswith('#'): return 0

    raw_cmd = _expand_vars(raw_cmd)
    try: parts = shlex.split(raw_cmd)
    except ValueError: parts = raw_cmd.split()
    if not parts: return 0

    command  = parts[0].lower()
    args_str = _expand_globs(' '.join(parts[1:])) if len(parts) > 1 else None
    stripped, flags = _strip_flags(args_str,
        {'-r','-f','-rf','-fr','--force','--recursive','-v','-n','-i','--interactive','--dry-run'})

    if args_str and any(t in ('-h','--help') for t in args_str.split()):
        HELP = {'rm':'rm [-r] [-f] <name>','ls':'ls [-l] [-a] [pattern]',
                'mkdir':'mkdir <dirname>','cd':'cd <path>','grep':'grep [-i] [-v] <pat> [file]'}
        print(HELP.get(command, f"No help for '{command}'")); return 0

    CMD = {
        'cd': lambda a: cd_command(a),
        'mkdir': mkdir_command, 'md': mkdir_command,
        'rmdir': rmdir_command, 'rd': rmdir_command,
        'mktf': mkfile_command, 'touch': mkfile_command,
        'mkef': mkexe_command,
        'vwtf': show_command, 'cat': show_command, 'type': show_command,
        'copy': copy_command, 'move': move_command, 'rem': rem_command,
        'edit': edit_command,
        'run': run_command, 'start': run_command,
        'install': install_command, 'uninstall': uninstall_command,
        'packages': packages_command, 'pkgs': packages_command,
        'pass': pass_command,
        'create': create_command, 'state': state_command,
        'echo': echo_command,
    }
    NO_ARGS = {
        'ls': ls_command, 'dir': ls_command,
        'help': help_command,
        'clear': clear_command, 'cls': clear_command,
        'sysinfo': sysinfo_command,
        'quit': quit_command, 'format': format_command, 'reboot': reboot_command,
        'packages': packages_command, 'pkgs': packages_command,
    }

    if command in ('ls', 'dir'):
        return ls_command(args_str) or 0
    elif command == 'echo':
        return echo_command(args_str) or 0
    elif command == 'grep':
        return grep_command(args_str) or 0
    elif command in ('rm', 'del'):
        return rm_command_ex(
            stripped,
            recursive=any(f in flags for f in ('-r','-rf','-fr','--recursive')),
            force=any(f in flags for f in ('-f','-rf','-fr','--force')),
            interactive='-i' in flags or '--interactive' in flags,
            dry_run='-n' in flags or '--dry-run' in flags
        ) or 0
    elif command in CMD:
        r = CMD[command](stripped); return r if isinstance(r, int) else 0
    elif command in NO_ARGS:
        r = NO_ARGS[command](); return r if isinstance(r, int) else 0
    else:
        r = _run_user_app(command)
        if r is not None: return r
        # fallback to real shell
        try:
            return subprocess.run(parts).returncode
        except FileNotFoundError:
            print(f"'{command}' is not recognized as an internal or external command")
            return 127

def _run_pipeline(segment):
    stages = _split_on_op(segment, '|')
    stdin_data = None; exit_code = 0
    for i, stage in enumerate(stages):
        stage    = stage.strip()
        is_last  = (i == len(stages) - 1)
        clean, redirects = _parse_redirects(stage)
        for op, target in redirects:
            if op == '<' and target:
                stdin_data = _read_vfile(target) or ''
        capture = not is_last or any(op in ('>','>>','&>','2>') for op, _ in redirects)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf if capture else sys.stdout):
            exit_code = _dispatch_single(clean, stdin_data)
        output = buf.getvalue() if capture else ''
        for op, target in redirects:
            if op in ('>','2>','&>') and target:
                _write_vfile(target, output, append=False); output=''
            elif op == '>>' and target:
                _write_vfile(target, output, append=True); output=''
        stdin_data = output if not is_last else None
        if is_last and output: print(output, end='')
    return exit_code

def process_commands():
    from ..display import check_input
    state.piped_input = None
    user_input = check_input()
    if not user_input.strip(): return
    if '#' in user_input:
        user_input = user_input[:user_input.index('#')]
    user_input = user_input.strip()
    if not user_input: return

    for group in _split_on_op(user_input, ';'):
        group = group.strip()
        if not group: continue
        segments, ops = [], []
        remaining = group
        while True:
            ai = remaining.find('&&')
            oi = remaining.find('||')
            if ai == -1 and oi == -1:
                segments.append(remaining); break
            if oi == -1 or (ai != -1 and ai < oi):
                segments.append(remaining[:ai]); ops.append('&&'); remaining = remaining[ai+2:]
            else:
                segments.append(remaining[:oi]); ops.append('||'); remaining = remaining[oi+2:]
        for i, seg in enumerate(segments):
            seg = seg.strip()
            if not seg: continue
            run = True if i == 0 else (state.last_exit == 0 if ops[i-1] == '&&' else state.last_exit != 0)
            if run:
                state.last_exit = _run_pipeline(seg)
