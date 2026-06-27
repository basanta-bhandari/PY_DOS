from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class State:
    current_directory: str = '/'
    last_exit: int = 0
    shell_vars: Dict[str, str] = field(default_factory=dict)
    piped_input: Any = None
    editor_open: bool = False
    sudo_cached: bool = False
    sys_profile: Dict = field(default_factory=dict)

state = State()

directory_contents: Dict[str, Any] = {}

kernel: Dict[str, Any] = {
    '/': {
        'type': 'directory',
        'contents': {
            'bin': {'type': 'directory', 'contents': {}},
            'usr': {'type': 'directory', 'contents': {}},
            'tmp': {'type': 'directory', 'contents': {}},
            'Apps': {
                'type': 'directory',
                'contents': {
                    'Games': {'type': 'directory', 'contents': {}},
                    'Utilities': {
                        'type': 'directory',
                        'contents': {
                            'Lynx':   {'type': 'directory', 'contents': {}},
                            'Mutiny': {'type': 'directory', 'contents': {}},
                        }
                    }
                }
            }
        }
    }
}

def normalize_path(path: str) -> str:
    if path.startswith('/'):
        parts = path.strip('/').split('/')
    else:
        parts = state.current_directory.strip('/').split('/')
        if state.current_directory == '/':
            parts = []
        parts.extend(path.split('/'))
    normalized = []
    for part in parts:
        if part == '..':
            if normalized:
                normalized.pop()
        elif part and part != '.':
            normalized.append(part)
    return '/' + '/'.join(normalized) if normalized else '/'

def join_path(base: str, name: str) -> str:
    if base == '/':
        return '/' + name
    return base + '/' + name

def get_dir_node(path: str = None):
    target = path or state.current_directory
    if target == '/':
        return kernel['/']
    node = kernel['/']
    for part in target.strip('/').split('/'):
        if 'contents' in node and part in node['contents']:
            node = node['contents'][part]
        else:
            return None
    return node

def reconcile_kernel_flat_index():
    def walk(node, path):
        kernel[path] = node
        for name, child in node.get('contents', {}).items():
            if child.get('type') == 'directory':
                child_path = path.rstrip('/') + '/' + name if path != '/' else '/' + name
                walk(child, child_path)
    walk(kernel['/'], '/')

def reset_kernel():
    global kernel, directory_contents
    kernel.clear()
    kernel['/'] = {
        'type': 'directory',
        'contents': {
            'bin': {'type': 'directory', 'contents': {}},
            'usr': {'type': 'directory', 'contents': {}},
            'tmp': {'type': 'directory', 'contents': {}},
        }
    }
    directory_contents.clear()
    state.current_directory = '/'
