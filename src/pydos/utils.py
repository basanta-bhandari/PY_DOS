import time
import sys
import random
import os
import platform
import json
import readchar
import atexit
import pickle
import hashlib
from pathlib import Path
import types
import tempfile
import psutil
from datetime import datetime
import threading
import subprocess
import shutil
import fnmatch
import contextlib
import io
import shlex
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None

FILESYSTEM_FILE = 'pydos_filesystem.json'
SAVED_FOLDER = 'saved'
AUTH_FILE = 'saved/pydos_auth.bin'

# Shell state
_last_exit  = 0        # $?
_shell_vars = {}       # $VAR
_piped_input = None    # data piped in from previous stage
_editor_open = False 
_sudo_cached = False
_sys_profile = {}
directory_contents = {}
current_directory = '/'
kernel = {
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
                        'Lynx': {'type': 'directory', 'contents': {}}
                    }
                }
                }
            }
        }
    }
}
PY_DOS = """
\n
\n
                            ██████╗ ██╗   ██╗    ██████╗  ██████╗ ███████╗
                            ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝
                            ██████╔╝ ╚████╔╝     ██║  ██║██║   ██║███████╗
                            ██╔═══╝   ╚██╔╝      ██║  ██║██║   ██║╚════██║
                            ██║        ██║       ██████╔╝╚██████╔╝███████║
                            ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚══════╝
\n
"""


LYNX_DIR = '/Apps/Utilities/Lynx'
LYNX_FILE = '/Apps/Utilities/Lynx/web'



from importlib import resources

def _seed_lynx_app():
    _ensure_lynx_kernel_path()
    if LYNX_FILE not in directory_contents:
        try:
            lynx_code = resources.files("pydos.appdata").joinpath("lynx.py").read_text(encoding="utf-8")
            directory_contents[LYNX_FILE] = {
                'type': 'exe',
                'content': lynx_code,
                'created_in': LYNX_DIR
            }
        except Exception as e:
            print(f"[Core] Failed to seed Lynx asset: {e}")
            return
    # kernel[LYNX_DIR] is intentionally the SAME object as the nested tree
    # node below (not a copy) — cd/ls only ever walk the nested 'contents'
    # tree, so writes to a separate dict here would be invisible to them.
    if 'web' not in kernel[LYNX_DIR].get('contents', {}):
        kernel[LYNX_DIR]['contents']['web'] = {'type': 'file'}

def _ensure_lynx_kernel_path():
    root_contents = kernel['/']['contents']
    if 'Apps' not in root_contents:
        root_contents['Apps'] = {'type': 'directory', 'contents': {}}
    apps_contents = root_contents['Apps']['contents']
    if 'Utilities' not in apps_contents:
        apps_contents['Utilities'] = {'type': 'directory', 'contents': {}}
    utils_contents = apps_contents['Utilities']['contents']
    if 'Lynx' not in utils_contents:
        utils_contents['Lynx'] = {'type': 'directory', 'contents': {}}
    kernel[LYNX_DIR] = utils_contents['Lynx']


MUTINY_DIR = '/Apps/Utilities/Mutiny'
MUTINY_SETUP_FILE = '/Apps/Utilities/Mutiny/setup'
MUTINY_COMMUNITY_FILE = '/Apps/Utilities/Mutiny/community'

def _ensure_mutiny_kernel_path():
    root_contents = kernel['/']['contents']
    if 'Apps' not in root_contents:
        root_contents['Apps'] = {'type': 'directory', 'contents': {}}
    apps_contents = root_contents['Apps']['contents']
    if 'Utilities' not in apps_contents:
        apps_contents['Utilities'] = {'type': 'directory', 'contents': {}}
    utils_contents = apps_contents['Utilities']['contents']
    if 'Mutiny' not in utils_contents:
        utils_contents['Mutiny'] = {'type': 'directory', 'contents': {}}
    kernel[MUTINY_DIR] = utils_contents['Mutiny']

def _seed_mutiny_app():
    _ensure_mutiny_kernel_path()
    try:
        mutiny_pkg = resources.files("pydos.appdata.mutiny")
        setup_code = mutiny_pkg.joinpath("setup.py").read_text(encoding="utf-8")
        community_code = mutiny_pkg.joinpath("community.py").read_text(encoding="utf-8")
    except Exception as e:
        print(f"[Core] Failed to seed Mutiny assets: {e}")
        return

    if MUTINY_SETUP_FILE not in directory_contents:
        directory_contents[MUTINY_SETUP_FILE] = {
            'type': 'exe', 'content': setup_code, 'created_in': MUTINY_DIR
        }
    if 'setup' not in kernel[MUTINY_DIR].get('contents', {}):
        kernel[MUTINY_DIR]['contents']['setup'] = {'type': 'file'}

    if MUTINY_COMMUNITY_FILE not in directory_contents:
        directory_contents[MUTINY_COMMUNITY_FILE] = {
            'type': 'exe', 'content': community_code, 'created_in': MUTINY_DIR
        }
    if 'community' not in kernel[MUTINY_DIR].get('contents', {}):
        kernel[MUTINY_DIR]['contents']['community'] = {'type': 'file'}



# ─── RubOS Engine (embedded) ─────────────────────────────────────────────────

RUBUS_ENGINE_SCRIPT = '"""\nRubOS — PY_DOS Rubus CLI Language Engine\nBASIC-inspired, geared for writing CLI tools inside PY_DOS.\n\nSyntax quick-reference:\n  let x = 5\n  let name = "hello"\n  let arr = [1, 2, 3]\n  println "Hello " + name\n  ask "Enter name: " -> name\n  if x > 3 then ... elif x > 1 then ... else ... end\n  while x > 0 do ... end\n  loop 5 times ... end\n  for i = 1 to 10 do ... end\n  def greet(name) ... return "hi " + name ... end\n  let r = greet("world")\n  append arr "item"\n  clear | pause | pause "msg" | color "cyan" | exit | exit 1\n  read_file "notes.txt" -> content\n  write_file "out.txt" content\n  list_dir -> files\n  menu ["Yes", "No"] -> choice\n  # this is a comment\n"""\n\nfrom dataclasses import dataclass, field\nfrom typing import Any, List, Optional\nimport sys\nimport os\n\n# ─── Errors ───────────────────────────────────────────────────────────────────\n\nclass RubosError(Exception):\n    def __init__(self, kind, message, line, source_lines=None):\n        self.kind = kind\n        self.message = message\n        self.line = line\n        self.source_lines = source_lines or []\n        super().__init__(self.format())\n\n    def format(self):\n        width = 54\n        bar = \'─\' * width\n        lines = [\n            f"┌─ RubOS {self.kind} {\'─\' * (width - len(self.kind) - 2)}┐",\n            f"│  Line {self.line:<{width-7}}│",\n        ]\n        if self.source_lines and 0 < self.line <= len(self.source_lines):\n            src = self.source_lines[self.line - 1].rstrip()\n            lines.append(f"│                                                      │")\n            snippet = f"  {self.line:>3} │  {src}"\n            lines.append(f"│  {snippet:<{width-2}}│")\n            lines.append(f"│                                                      │")\n        lines.append(f"│  {self.message:<{width-2}}│")\n        lines.append(f"└{\'─\' * width}┘")\n        return \'\\n\'.join(lines)\n\nclass ReturnSignal(Exception):\n    def __init__(self, value): self.value = value\n\nclass ExitSignal(Exception):\n    def __init__(self, code=0): self.code = code\n\n# ─── Tokens ───────────────────────────────────────────────────────────────────\n\nKEYWORDS = {\n    \'let\',\'if\',\'elif\',\'else\',\'then\',\'end\',\'while\',\'do\',\'loop\',\'times\',\n    \'for\',\'to\',\'def\',\'return\',\'and\',\'or\',\'not\',\'true\',\'false\',\n    \'print\',\'println\',\'ask\',\'clear\',\'pause\',\'color\',\'exit\',\n    \'read_file\',\'write_file\',\'list_dir\',\'menu\',\'append\',\'len\',\n}\n\n@dataclass\nclass Token:\n    type: str   # KW IDENT NUM STR OP ARROW LPAREN RPAREN LBRACK RBRACK COMMA NEWLINE EOF\n    value: Any\n    line: int\n\ndef tokenize(source):\n    tokens = []\n    lines = source.split(\'\\n\')\n    i = 0\n    src_len = len(source)\n    line_no = 1\n\n    def peek(n=1): return source[i:i+n] if i+n <= src_len else \'\'\n    def add(t, v, ln): tokens.append(Token(t, v, ln))\n\n    while i < src_len:\n        c = source[i]\n\n        # Newline\n        if c == \'\\n\':\n            if not tokens or tokens[-1].type != \'NEWLINE\':\n                add(\'NEWLINE\', \'\\n\', line_no)\n            line_no += 1\n            i += 1\n            continue\n\n        # Whitespace (not newline)\n        if c in \' \\t\\r\':\n            i += 1\n            continue\n\n        # Comment\n        if c == \'#\':\n            while i < src_len and source[i] != \'\\n\':\n                i += 1\n            continue\n\n        # String\n        if c in (\'"\', "\'"):\n            quote = c\n            i += 1\n            buf = []\n            start_line = line_no\n            while i < src_len and source[i] != quote:\n                if source[i] == \'\\\\\':\n                    i += 1\n                    esc = source[i] if i < src_len else \'\'\n                    buf.append({\'n\':\'\\n\',\'t\':\'\\t\',\'\\\\\':\'\\\\\',\'"\':\'"\',"\'":"\'"}.get(esc, esc))\n                else:\n                    buf.append(source[i])\n                if source[i] == \'\\n\': line_no += 1\n                i += 1\n            if i >= src_len:\n                raise RubosError("SyntaxError", "Unterminated string literal", start_line, lines)\n            i += 1\n            add(\'STR\', \'\'.join(buf), start_line)\n            continue\n\n        # Number\n        if c.isdigit() or (c == \'-\' and source[i+1:i+2].isdigit() and (not tokens or tokens[-1].type in (\'NEWLINE\',\'OP\',\'LPAREN\',\'LBRACK\',\'COMMA\',\'KW\'))):\n            buf = [c]; i += 1\n            while i < src_len and (source[i].isdigit() or source[i] == \'.\'):\n                buf.append(source[i]); i += 1\n            val = float(\'\'.join(buf)) if \'.\' in buf else int(\'\'.join(buf))\n            add(\'NUM\', val, line_no)\n            continue\n\n        # Arrow ->\n        if c == \'-\' and peek(2) == \'->\':\n            add(\'ARROW\', \'->\', line_no); i += 2; continue\n\n        # Two-char operators\n        two = peek(2)\n        if two in (\'==\',\'!=\',\'<=\',\'>=\',\'->\',\'..\'):\n            add(\'OP\', two, line_no); i += 2; continue\n\n        # Single-char operators and punctuation\n        if c in \'+-*/%<>\':\n            add(\'OP\', c, line_no); i += 1; continue\n        if c == \'=\':\n            add(\'OP\', \'=\', line_no); i += 1; continue\n        if c == \'(\':\n            add(\'LPAREN\', \'(\', line_no); i += 1; continue\n        if c == \')\':\n            add(\'RPAREN\', \')\', line_no); i += 1; continue\n        if c == \'[\':\n            add(\'LBRACK\', \'[\', line_no); i += 1; continue\n        if c == \']\':\n            add(\'RBRACK\', \']\', line_no); i += 1; continue\n        if c == \',\':\n            add(\'COMMA\', \',\', line_no); i += 1; continue\n\n        # Identifier or keyword\n        if c.isalpha() or c == \'_\':\n            buf = []\n            while i < src_len and (source[i].isalnum() or source[i] == \'_\'):\n                buf.append(source[i]); i += 1\n            word = \'\'.join(buf)\n            if word in KEYWORDS:\n                add(\'KW\', word, line_no)\n            else:\n                add(\'IDENT\', word, line_no)\n            continue\n\n        raise RubosError("SyntaxError", f"Unexpected character: \'{c}\'", line_no, lines)\n\n    add(\'EOF\', None, line_no)\n    return tokens\n\n# ─── AST Nodes ────────────────────────────────────────────────────────────────\n\n@dataclass\nclass LetStmt:\n    name: str; expr: Any; line: int\n\n@dataclass\nclass AssignIndexStmt:\n    name: str; index: Any; expr: Any; line: int\n\n@dataclass\nclass PrintStmt:\n    expr: Any; newline: bool; line: int\n\n@dataclass\nclass AskStmt:\n    prompt: Any; var: str; line: int\n\n@dataclass\nclass IfStmt:\n    cond: Any; body: List; elifs: List; else_body: List; line: int\n\n@dataclass\nclass WhileStmt:\n    cond: Any; body: List; line: int\n\n@dataclass\nclass LoopTimesStmt:\n    count: Any; body: List; line: int\n\n@dataclass\nclass ForStmt:\n    var: str; start: Any; end: Any; body: List; line: int\n\n@dataclass\nclass DefStmt:\n    name: str; params: List[str]; body: List; line: int\n\n@dataclass\nclass ReturnStmt:\n    expr: Any; line: int\n\n@dataclass\nclass CallStmt:\n    name: str; args: List; line: int\n\n@dataclass\nclass AppendStmt:\n    arr: str; val: Any; line: int\n\n@dataclass\nclass ClearStmt:\n    line: int\n\n@dataclass\nclass PauseStmt:\n    msg: Any; line: int\n\n@dataclass\nclass ColorStmt:\n    color: Any; line: int\n\n@dataclass\nclass ExitStmt:\n    code: Any; line: int\n\n@dataclass\nclass ReadFileStmt:\n    filename: Any; var: str; line: int\n\n@dataclass\nclass WriteFileStmt:\n    filename: Any; expr: Any; line: int\n\n@dataclass\nclass ListDirStmt:\n    var: str; line: int\n\n@dataclass\nclass MenuStmt:\n    options: Any; var: str; line: int\n\n# Expressions\n@dataclass\nclass BinOp:\n    op: str; left: Any; right: Any; line: int\n\n@dataclass\nclass UnaryOp:\n    op: str; operand: Any; line: int\n\n@dataclass\nclass Literal:\n    value: Any; line: int\n\n@dataclass\nclass VarRef:\n    name: str; line: int\n\n@dataclass\nclass CallExpr:\n    name: str; args: List; line: int\n\n@dataclass\nclass IndexExpr:\n    obj: Any; index: Any; line: int\n\n@dataclass\nclass ListLiteral:\n    items: List; line: int\n\n@dataclass\nclass LenExpr:\n    expr: Any; line: int\n\n# ─── Parser ───────────────────────────────────────────────────────────────────\n\nclass Parser:\n    def __init__(self, tokens, source_lines):\n        self.tokens = tokens\n        self.pos = 0\n        self.src = source_lines\n\n    def cur(self): return self.tokens[self.pos]\n    def peek(self, n=1): return self.tokens[min(self.pos+n, len(self.tokens)-1)]\n\n    def eat(self, type_=None, value=None):\n        t = self.cur()\n        if type_ and t.type != type_:\n            raise RubosError("SyntaxError",\n                f"Expected {type_} but got {t.type} \'{t.value}\'", t.line, self.src)\n        if value and t.value != value:\n            raise RubosError("SyntaxError",\n                f"Expected \'{value}\' but got \'{t.value}\'", t.line, self.src)\n        self.pos += 1\n        return t\n\n    def skip_newlines(self):\n        while self.cur().type == \'NEWLINE\':\n            self.pos += 1\n\n    def eat_newline(self):\n        if self.cur().type == \'NEWLINE\':\n            self.pos += 1\n        elif self.cur().type != \'EOF\':\n            raise RubosError("SyntaxError",\n                f"Expected end of line but got \'{self.cur().value}\'",\n                self.cur().line, self.src)\n\n    def parse(self):\n        self.skip_newlines()\n        stmts = []\n        while self.cur().type != \'EOF\':\n            stmts.append(self.parse_stmt())\n            self.skip_newlines()\n        return stmts\n\n    def parse_block(self, *stop_kws):\n        """Parse statements until a keyword in stop_kws."""\n        stmts = []\n        self.skip_newlines()\n        while self.cur().type != \'EOF\':\n            if self.cur().type == \'KW\' and self.cur().value in stop_kws:\n                break\n            stmts.append(self.parse_stmt())\n            self.skip_newlines()\n        return stmts\n\n    def parse_stmt(self):\n        t = self.cur()\n\n        if t.type == \'NEWLINE\':\n            self.pos += 1\n            return self.parse_stmt()\n\n        if t.type == \'KW\':\n            if t.value == \'let\':         return self.parse_let()\n            if t.value in (\'print\',\'println\'): return self.parse_print()\n            if t.value == \'ask\':         return self.parse_ask()\n            if t.value == \'if\':          return self.parse_if()\n            if t.value == \'while\':       return self.parse_while()\n            if t.value == \'loop\':        return self.parse_loop()\n            if t.value == \'for\':         return self.parse_for()\n            if t.value == \'def\':         return self.parse_def()\n            if t.value == \'return\':      return self.parse_return()\n            if t.value == \'append\':      return self.parse_append()\n            if t.value == \'clear\':       ln=t.line; self.pos+=1; self.eat_newline(); return ClearStmt(ln)\n            if t.value == \'pause\':       return self.parse_pause()\n            if t.value == \'color\':       return self.parse_color()\n            if t.value == \'exit\':        return self.parse_exit()\n            if t.value == \'read_file\':   return self.parse_read_file()\n            if t.value == \'write_file\':  return self.parse_write_file()\n            if t.value == \'list_dir\':    return self.parse_list_dir()\n            if t.value == \'menu\':        return self.parse_menu()\n\n        # Function call as statement: name(args)\n        if t.type == \'IDENT\' and self.peek().type == \'LPAREN\':\n            return self.parse_call_stmt()\n\n        raise RubosError("SyntaxError", f"Unexpected token \'{t.value}\'", t.line, self.src)\n\n    def parse_let(self):\n        ln = self.cur().line; self.eat(\'KW\',\'let\')\n        name = self.eat(\'IDENT\').value\n        self.eat(\'OP\',\'=\')\n        expr = self.parse_expr()\n        self.eat_newline()\n        return LetStmt(name, expr, ln)\n\n    def parse_print(self):\n        t = self.eat(\'KW\'); ln = t.line\n        newline = (t.value == \'println\')\n        expr = self.parse_expr()\n        self.eat_newline()\n        return PrintStmt(expr, newline, ln)\n\n    def parse_ask(self):\n        ln = self.cur().line; self.eat(\'KW\',\'ask\')\n        prompt = self.parse_expr()\n        self.eat(\'ARROW\')\n        var = self.eat(\'IDENT\').value\n        self.eat_newline()\n        return AskStmt(prompt, var, ln)\n\n    def parse_if(self):\n        ln = self.cur().line; self.eat(\'KW\',\'if\')\n        cond = self.parse_expr()\n        self.eat(\'KW\',\'then\'); self.eat_newline()\n        body = self.parse_block(\'elif\',\'else\',\'end\')\n        elifs = []\n        while self.cur().type == \'KW\' and self.cur().value == \'elif\':\n            self.pos += 1\n            ec = self.parse_expr(); self.eat(\'KW\',\'then\'); self.eat_newline()\n            eb = self.parse_block(\'elif\',\'else\',\'end\')\n            elifs.append((ec, eb))\n        else_body = []\n        if self.cur().type == \'KW\' and self.cur().value == \'else\':\n            self.pos += 1; self.eat_newline()\n            else_body = self.parse_block(\'end\')\n        self.eat(\'KW\',\'end\'); self.eat_newline()\n        return IfStmt(cond, body, elifs, else_body, ln)\n\n    def parse_while(self):\n        ln = self.cur().line; self.eat(\'KW\',\'while\')\n        cond = self.parse_expr(); self.eat(\'KW\',\'do\'); self.eat_newline()\n        body = self.parse_block(\'end\')\n        self.eat(\'KW\',\'end\'); self.eat_newline()\n        return WhileStmt(cond, body, ln)\n\n    def parse_loop(self):\n        ln = self.cur().line; self.eat(\'KW\',\'loop\')\n        count = self.parse_expr(); self.eat(\'KW\',\'times\'); self.eat_newline()\n        body = self.parse_block(\'end\')\n        self.eat(\'KW\',\'end\'); self.eat_newline()\n        return LoopTimesStmt(count, body, ln)\n\n    def parse_for(self):\n        ln = self.cur().line; self.eat(\'KW\',\'for\')\n        var = self.eat(\'IDENT\').value; self.eat(\'OP\',\'=\')\n        start = self.parse_expr(); self.eat(\'KW\',\'to\')\n        end = self.parse_expr()\n        if self.cur().type == \'KW\' and self.cur().value == \'do\':\n            self.pos += 1  # optional \'do\'\n        self.eat_newline()\n        body = self.parse_block(\'end\')\n        self.eat(\'KW\',\'end\'); self.eat_newline()\n        return ForStmt(var, start, end, body, ln)\n\n    def parse_def(self):\n        ln = self.cur().line; self.eat(\'KW\',\'def\')\n        name = self.eat(\'IDENT\').value; self.eat(\'LPAREN\')\n        params = []\n        while self.cur().type != \'RPAREN\':\n            params.append(self.eat(\'IDENT\').value)\n            if self.cur().type == \'COMMA\': self.pos += 1\n        self.eat(\'RPAREN\'); self.eat_newline()\n        body = self.parse_block(\'end\')\n        self.eat(\'KW\',\'end\'); self.eat_newline()\n        return DefStmt(name, params, body, ln)\n\n    def parse_return(self):\n        ln = self.cur().line; self.eat(\'KW\',\'return\')\n        expr = None\n        if self.cur().type not in (\'NEWLINE\',\'EOF\'):\n            expr = self.parse_expr()\n        self.eat_newline()\n        return ReturnStmt(expr, ln)\n\n    def parse_call_stmt(self):\n        ln = self.cur().line\n        name = self.eat(\'IDENT\').value; self.eat(\'LPAREN\')\n        args = self.parse_args(); self.eat(\'RPAREN\'); self.eat_newline()\n        return CallStmt(name, args, ln)\n\n    def parse_append(self):\n        ln = self.cur().line; self.eat(\'KW\',\'append\')\n        arr = self.eat(\'IDENT\').value\n        val = self.parse_expr(); self.eat_newline()\n        return AppendStmt(arr, val, ln)\n\n    def parse_pause(self):\n        ln = self.cur().line; self.eat(\'KW\',\'pause\')\n        msg = None\n        if self.cur().type not in (\'NEWLINE\',\'EOF\'):\n            msg = self.parse_expr()\n        self.eat_newline()\n        return PauseStmt(msg, ln)\n\n    def parse_color(self):\n        ln = self.cur().line; self.eat(\'KW\',\'color\')\n        c = self.parse_expr(); self.eat_newline()\n        return ColorStmt(c, ln)\n\n    def parse_exit(self):\n        ln = self.cur().line; self.eat(\'KW\',\'exit\')\n        code = None\n        if self.cur().type not in (\'NEWLINE\',\'EOF\'):\n            code = self.parse_expr()\n        self.eat_newline()\n        return ExitStmt(code, ln)\n\n    def parse_read_file(self):\n        ln = self.cur().line; self.eat(\'KW\',\'read_file\')\n        fn = self.parse_expr(); self.eat(\'ARROW\')\n        var = self.eat(\'IDENT\').value; self.eat_newline()\n        return ReadFileStmt(fn, var, ln)\n\n    def parse_write_file(self):\n        ln = self.cur().line; self.eat(\'KW\',\'write_file\')\n        fn = self.parse_expr()\n        expr = self.parse_expr(); self.eat_newline()\n        return WriteFileStmt(fn, expr, ln)\n\n    def parse_list_dir(self):\n        ln = self.cur().line; self.eat(\'KW\',\'list_dir\')\n        self.eat(\'ARROW\'); var = self.eat(\'IDENT\').value; self.eat_newline()\n        return ListDirStmt(var, ln)\n\n    def parse_menu(self):\n        ln = self.cur().line; self.eat(\'KW\',\'menu\')\n        opts = self.parse_expr(); self.eat(\'ARROW\')\n        var = self.eat(\'IDENT\').value; self.eat_newline()\n        return MenuStmt(opts, var, ln)\n\n    def parse_args(self):\n        args = []\n        while self.cur().type not in (\'RPAREN\',\'RBRACK\',\'EOF\'):\n            args.append(self.parse_expr())\n            if self.cur().type == \'COMMA\': self.pos += 1\n        return args\n\n    # Expression parsing (recursive descent)\n    def parse_expr(self):   return self.parse_or()\n    def parse_or(self):\n        left = self.parse_and()\n        while self.cur().type == \'KW\' and self.cur().value == \'or\':\n            ln = self.cur().line; self.pos += 1\n            left = BinOp(\'or\', left, self.parse_and(), ln)\n        return left\n    def parse_and(self):\n        left = self.parse_not()\n        while self.cur().type == \'KW\' and self.cur().value == \'and\':\n            ln = self.cur().line; self.pos += 1\n            left = BinOp(\'and\', left, self.parse_not(), ln)\n        return left\n    def parse_not(self):\n        if self.cur().type == \'KW\' and self.cur().value == \'not\':\n            ln = self.cur().line; self.pos += 1\n            return UnaryOp(\'not\', self.parse_not(), ln)\n        return self.parse_compare()\n    def parse_compare(self):\n        left = self.parse_add()\n        if self.cur().type == \'OP\' and self.cur().value in (\'==\',\'!=\',\'<\',\'>\',\'<=\',\'>=\'):\n            ln = self.cur().line; op = self.cur().value; self.pos += 1\n            return BinOp(op, left, self.parse_add(), ln)\n        return left\n    def parse_add(self):\n        left = self.parse_mul()\n        while self.cur().type == \'OP\' and self.cur().value in (\'+\',\'-\'):\n            ln = self.cur().line; op = self.cur().value; self.pos += 1\n            left = BinOp(op, left, self.parse_mul(), ln)\n        return left\n    def parse_mul(self):\n        left = self.parse_unary()\n        while self.cur().type == \'OP\' and self.cur().value in (\'*\',\'/\',\'%\'):\n            ln = self.cur().line; op = self.cur().value; self.pos += 1\n            left = BinOp(op, left, self.parse_unary(), ln)\n        return left\n    def parse_unary(self):\n        if self.cur().type == \'OP\' and self.cur().value == \'-\':\n            ln = self.cur().line; self.pos += 1\n            return UnaryOp(\'-\', self.parse_unary(), ln)\n        return self.parse_primary()\n    def parse_primary(self):\n        t = self.cur(); ln = t.line\n        if t.type == \'NUM\':  self.pos += 1; return Literal(t.value, ln)\n        if t.type == \'STR\':  self.pos += 1; return Literal(t.value, ln)\n        if t.type == \'KW\' and t.value == \'true\':  self.pos += 1; return Literal(True, ln)\n        if t.type == \'KW\' and t.value == \'false\': self.pos += 1; return Literal(False, ln)\n        if t.type == \'LBRACK\':\n            self.pos += 1\n            items = self.parse_args()\n            self.eat(\'RBRACK\')\n            return ListLiteral(items, ln)\n        if t.type == \'KW\' and t.value == \'len\':\n            self.pos += 1; self.eat(\'LPAREN\')\n            expr = self.parse_expr(); self.eat(\'RPAREN\')\n            return LenExpr(expr, ln)\n        if t.type == \'IDENT\':\n            name = t.value; self.pos += 1\n            if self.cur().type == \'LPAREN\':\n                self.eat(\'LPAREN\'); args = self.parse_args(); self.eat(\'RPAREN\')\n                node = CallExpr(name, args, ln)\n            else:\n                node = VarRef(name, ln)\n            if self.cur().type == \'LBRACK\':\n                self.pos += 1; idx = self.parse_expr(); self.eat(\'RBRACK\')\n                return IndexExpr(node, idx, ln)\n            return node\n        if t.type == \'LPAREN\':\n            self.pos += 1; expr = self.parse_expr(); self.eat(\'RPAREN\')\n            return expr\n        raise RubosError("SyntaxError", f"Unexpected \'{t.value}\' in expression", ln, [])\n\n# ─── Interpreter ──────────────────────────────────────────────────────────────\n\nCOLORS = {\n    \'red\':\'\\033[31m\',\'green\':\'\\033[32m\',\'yellow\':\'\\033[33m\',\'blue\':\'\\033[34m\',\n    \'magenta\':\'\\033[35m\',\'cyan\':\'\\033[36m\',\'white\':\'\\033[37m\',\'reset\':\'\\033[0m\',\n    \'bold\':\'\\033[1m\',\n}\n\nclass Interpreter:\n    def __init__(self, source_lines, ctx):\n        self.src = source_lines\n        self.ctx = ctx\n        self.globals = {}\n        self.call_stack = []  # list of local env dicts\n\n    def env(self): return self.call_stack[-1] if self.call_stack else self.globals\n\n    def get(self, name, line):\n        for frame in reversed(self.call_stack):\n            if name in frame: return frame[name]\n        if name in self.globals: return self.globals[name]\n        raise RubosError("NameError", f"Variable \'{name}\' is not defined", line, self.src)\n\n    def set(self, name, value):\n        if self.call_stack:\n            self.call_stack[-1][name] = value\n        else:\n            self.globals[name] = value\n\n    def run(self, stmts):\n        for stmt in stmts:\n            self.exec(stmt)\n\n    def exec(self, node):\n        t = type(node)\n\n        if t is LetStmt:\n            self.set(node.name, self.eval(node.expr))\n\n        elif t is PrintStmt:\n            val = self.eval(node.expr)\n            end = \'\\n\' if node.newline else \'\'\n            print(self._to_str(val), end=end)\n\n        elif t is AskStmt:\n            prompt = self._to_str(self.eval(node.prompt))\n            val = input(prompt)\n            self.set(node.var, val)\n\n        elif t is IfStmt:\n            if self._truthy(self.eval(node.cond)):\n                self.run(node.body)\n            else:\n                done = False\n                for ec, eb in node.elifs:\n                    if self._truthy(self.eval(ec)):\n                        self.run(eb); done = True; break\n                if not done:\n                    self.run(node.else_body)\n\n        elif t is WhileStmt:\n            limit = 100_000; count = 0\n            while self._truthy(self.eval(node.cond)):\n                self.run(node.body)\n                count += 1\n                if count >= limit:\n                    raise RubosError("RuntimeError", "Loop exceeded 100,000 iterations (infinite loop?)", node.line, self.src)\n\n        elif t is LoopTimesStmt:\n            n = self.eval(node.count)\n            if not isinstance(n, (int, float)):\n                raise RubosError("TypeError", f"\'loop N times\' expects a number, got {type(n).__name__}", node.line, self.src)\n            for _ in range(int(n)):\n                self.run(node.body)\n\n        elif t is ForStmt:\n            start = self.eval(node.start); end = self.eval(node.end)\n            for i in range(int(start), int(end)+1):\n                self.set(node.var, i)\n                self.run(node.body)\n\n        elif t is DefStmt:\n            self.globals[node.name] = node\n\n        elif t is ReturnStmt:\n            val = self.eval(node.expr) if node.expr else None\n            raise ReturnSignal(val)\n\n        elif t is CallStmt:\n            self._call(node.name, node.args, node.line)\n\n        elif t is AppendStmt:\n            arr = self.get(node.arr, node.line)\n            if not isinstance(arr, list):\n                raise RubosError("TypeError", f"\'append\' expects a list, got {type(arr).__name__}", node.line, self.src)\n            arr.append(self.eval(node.val))\n\n        elif t is ClearStmt:\n            self.ctx.clear()\n\n        elif t is PauseStmt:\n            msg = self._to_str(self.eval(node.msg)) if node.msg else "Press Enter to continue..."\n            input(msg)\n\n        elif t is ColorStmt:\n            c = self._to_str(self.eval(node.color)).lower()\n            print(COLORS.get(c, \'\'), end=\'\')\n\n        elif t is ExitStmt:\n            code = int(self.eval(node.code)) if node.code else 0\n            raise ExitSignal(code)\n\n        elif t is ReadFileStmt:\n            fn = self._to_str(self.eval(node.filename))\n            content = self.ctx.read_file(fn)\n            if content is None:\n                raise RubosError("IOError", f"File not found: \'{fn}\'", node.line, self.src)\n            self.set(node.var, content)\n\n        elif t is WriteFileStmt:\n            fn = self._to_str(self.eval(node.filename))\n            content = self._to_str(self.eval(node.expr))\n            self.ctx.write_file(fn, content)\n\n        elif t is ListDirStmt:\n            self.set(node.var, self.ctx.list_dir())\n\n        elif t is MenuStmt:\n            opts = self.eval(node.options)\n            if not isinstance(opts, list) or not opts:\n                raise RubosError("TypeError", "\'menu\' expects a non-empty list", node.line, self.src)\n            for i, o in enumerate(opts, 1):\n                print(f"  {i}) {self._to_str(o)}")\n            while True:\n                try:\n                    raw = input("Choice: ").strip()\n                    idx = int(raw) - 1\n                    if 0 <= idx < len(opts):\n                        self.set(node.var, opts[idx])\n                        break\n                    print(f"  Enter a number between 1 and {len(opts)}")\n                except ValueError:\n                    print(f"  Enter a number between 1 and {len(opts)}")\n\n    def eval(self, node):\n        t = type(node)\n        if t is Literal:  return node.value\n        if t is VarRef:   return self.get(node.name, node.line)\n        if t is ListLiteral: return [self.eval(i) for i in node.items]\n        if t is LenExpr:\n            v = self.eval(node.expr)\n            if not isinstance(v, (list, str)):\n                raise RubosError("TypeError", f"\'len\' expects string or list, got {type(v).__name__}", node.line, self.src)\n            return len(v)\n        if t is IndexExpr:\n            obj = self.eval(node.obj); idx = self.eval(node.index)\n            if not isinstance(obj, (list, str)):\n                raise RubosError("TypeError", f"Can only index into list or string", node.line, self.src)\n            if not isinstance(idx, (int, float)):\n                raise RubosError("TypeError", f"Index must be a number", node.line, self.src)\n            i = int(idx)\n            if i < 0 or i >= len(obj):\n                raise RubosError("IndexError", f"Index {i} out of range (length {len(obj)})", node.line, self.src)\n            return obj[i]\n        if t is CallExpr:\n            return self._call(node.name, node.args, node.line)\n        if t is UnaryOp:\n            v = self.eval(node.operand)\n            if node.op == \'-\':\n                if not isinstance(v, (int, float)):\n                    raise RubosError("TypeError", f"Cannot negate {type(v).__name__}", node.line, self.src)\n                return -v\n            if node.op == \'not\': return not self._truthy(v)\n        if t is BinOp:\n            return self._binop(node)\n        raise RubosError("InternalError", f"Unknown AST node: {t.__name__}", 0, self.src)\n\n    def _binop(self, node):\n        op = node.op\n        # Short-circuit logic\n        if op == \'and\':\n            return self._truthy(self.eval(node.left)) and self._truthy(self.eval(node.right))\n        if op == \'or\':\n            return self._truthy(self.eval(node.left)) or self._truthy(self.eval(node.right))\n\n        left = self.eval(node.left); right = self.eval(node.right)\n        ln = node.line\n\n        if op == \'+\':\n            if isinstance(left, (int, float)) and isinstance(right, (int, float)):\n                return left + right\n            return self._to_str(left) + self._to_str(right)  # string concat\n\n        if op == \'-\':\n            self._assert_num(left, right, \'-\', ln)\n            return left - right\n        if op == \'*\':\n            self._assert_num(left, right, \'*\', ln)\n            return left * right\n        if op == \'/\':\n            self._assert_num(left, right, \'/\', ln)\n            if right == 0:\n                raise RubosError("ZeroDivisionError", "Cannot divide by zero", ln, self.src)\n            return left / right\n        if op == \'%\':\n            self._assert_num(left, right, \'%\', ln)\n            if right == 0:\n                raise RubosError("ZeroDivisionError", "Cannot modulo by zero", ln, self.src)\n            return left % right\n        if op == \'==\': return left == right\n        if op == \'!=\': return left != right\n        if op == \'<\':  return left < right\n        if op == \'>\':  return left > right\n        if op == \'<=\': return left <= right\n        if op == \'>=\': return left >= right\n        raise RubosError("SyntaxError", f"Unknown operator \'{op}\'", ln, self.src)\n\n    def _call(self, name, arg_nodes, line):\n        func = self.globals.get(name)\n        if func is None:\n            raise RubosError("NameError", f"Function \'{name}\' is not defined", line, self.src)\n        if not isinstance(func, DefStmt):\n            raise RubosError("TypeError", f"\'{name}\' is not a function", line, self.src)\n        args = [self.eval(a) for a in arg_nodes]\n        if len(args) != len(func.params):\n            raise RubosError("TypeError",\n                f"\'{name}\' expects {len(func.params)} argument(s), got {len(args)}", line, self.src)\n        frame = dict(zip(func.params, args))\n        self.call_stack.append(frame)\n        try:\n            self.run(func.body)\n            return None\n        except ReturnSignal as r:\n            return r.value\n        finally:\n            self.call_stack.pop()\n\n    def _assert_num(self, a, b, op, line):\n        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n            raise RubosError("TypeError",\n                f"Operator \'{op}\' requires numbers, got {type(a).__name__} and {type(b).__name__}",\n                line, self.src)\n\n    def _truthy(self, v):\n        if v is None: return False\n        if isinstance(v, bool): return v\n        if isinstance(v, (int, float)): return v != 0\n        if isinstance(v, str): return v != \'\'\n        if isinstance(v, list): return len(v) > 0\n        return True\n\n    def _to_str(self, v):\n        if isinstance(v, bool): return \'true\' if v else \'false\'\n        if isinstance(v, float):\n            return str(int(v)) if v == int(v) else str(v)\n        if isinstance(v, list):\n            return \'[\' + \', \'.join(self._to_str(i) for i in v) + \']\'\n        return str(v) if v is not None else \'\'\n\n# ─── Public API ───────────────────────────────────────────────────────────────\n\nclass PYDOSContext:\n    """Passed to the interpreter so it can interact with PY_DOS\'s virtual FS."""\n    def __init__(self, directory_contents, kernel, current_directory,\n                 join_path, save_file_contents, save_filesystem):\n        self._dc  = directory_contents\n        self._k   = kernel\n        self._cwd = current_directory\n        self._jp  = join_path\n        self._sfc = save_file_contents\n        self._sf  = save_filesystem\n\n    def read_file(self, name):\n        p = self._jp(self._cwd, name)\n        if p in self._dc:\n            return self._dc[p].get(\'content\', \'\')\n        return None\n\n    def write_file(self, name, content):\n        p = self._jp(self._cwd, name)\n        self._dc[p] = {\'type\': \'txt\', \'content\': content, \'created_in\': self._cwd}\n        self._k[self._cwd][\'contents\'][name] = {\'type\': \'file\'}\n        self._sfc(); self._sf()\n\n    def list_dir(self):\n        node = self._k.get(self._cwd, {})\n        return list(node.get(\'contents\', {}).keys())\n\n    def clear(self):\n        os.system(\'clear\')\n\n\ndef run(source, ctx=None):\n    """\n    Compile and run a RubOS program.\n    Returns exit code (0=success, nonzero=error/exit).\n    ctx: PYDOSContext or None (for standalone testing).\n    """\n    if ctx is None:\n        # Minimal stub for running outside PY_DOS\n        class _StubCtx:\n            def read_file(self, n): return None\n            def write_file(self, n, c): pass\n            def list_dir(self): return []\n            def clear(self): print(\'\\033[2J\\033[H\', end=\'\')\n        ctx = _StubCtx()\n\n    source_lines = source.split(\'\\n\')\n    try:\n        tokens = tokenize(source)\n        parser = Parser(tokens, source_lines)\n        ast = parser.parse()\n        interp = Interpreter(source_lines, ctx)\n        interp.run(ast)\n        return 0\n    except RubosError as e:\n        print(str(e))\n        return 1\n    except ExitSignal as e:\n        return e.code\n    except KeyboardInterrupt:\n        print(\'\\n[RubOS] Interrupted.\')\n        return 130\n    except RecursionError:\n        print(RubosError("RuntimeError", "Stack overflow — infinite recursion?", 0, source_lines))\n        return 1\n\n\ndef check(source):\n    """Parse only (no execution). Returns list of error strings, empty = OK."""\n    source_lines = source.split(\'\\n\')\n    errors = []\n    try:\n        tokens = tokenize(source)\n        parser = Parser(tokens, source_lines)\n        parser.parse()\n    except RubosError as e:\n        errors.append(str(e))\n    return errors\n\n\n# Run as standalone script for testing\nif __name__ == \'__main__\':\n    if len(sys.argv) < 2:\n        print("Usage: rubus_engine.py <file.rub>")\n        sys.exit(1)\n    src = open(sys.argv[1]).read()\n    sys.exit(run(src))\n'

_rubus_module = None

def _get_rubus():
    """Load the RubOS engine, preferring the installed package but falling back
    to the embedded copy so it works before pip install -e . is done."""
    global _rubus_module
    if _rubus_module is not None:
        return _rubus_module
    try:
        from pydos.appdata import rubus_engine
        _rubus_module = rubus_engine
    except ImportError:
        import types as _types
        m = _types.ModuleType('rubus_engine')
        exec(compile(RUBUS_ENGINE_SCRIPT, 'rubus_engine.py', 'exec'), m.__dict__)
        _rubus_module = m
    return _rubus_module

# ─── User App constants ───────────────────────────────────────────────────────

USER_APPS_DIR = '/Apps/User'
_APP_TEMPLATE = '# My PY_DOS App\n# RubOS CLI Language — type \'state <appname>\' to check for errors\n#\n# Quick reference:\n#   let x = 5           variables\n#   println "hello"     print with newline\n#   ask "Name: " -> n   user input\n#   if x > 3 then ... elif ... else ... end\n#   while cond do ... end\n#   loop 5 times ... end\n#   for i = 1 to 10 do ... end\n#   def myfunc(a, b) ... return a+b ... end\n#   let r = myfunc(1, 2)\n#   append mylist val   add to list\n#   clear | pause | color "cyan" | exit\n#   read_file "f.txt" -> content\n#   write_file "f.txt" content\n#   list_dir -> files   get list of files in current dir\n#   menu ["A","B"] -> choice\n\nprintln "Hello from my app!"\nask "Press Enter to continue..." -> _\n'

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
    fpath = USER_APPS_DIR + '/' + name + '/main.rub'
    return directory_contents.get(fpath, {}).get('content')

def create_command(args):
    """create -cli <name>  — scaffold a new CLI app."""
    if not args:
        print("Usage: create -cli <appname>")
        return 1
    parts = args.split()
    if len(parts) < 2 or parts[0] != '-cli':
        print("Usage: create -cli <appname>")
        return 1
    name = parts[1].strip().lower().replace(' ', '_')
    if not name.isidentifier():
        print(f"App name '{name}' is invalid. Use letters, digits, and underscores only.")
        return 1
    _ensure_user_apps_dir()
    user_apps = kernel[USER_APPS_DIR]['contents']
    if name in user_apps:
        print(f"App '{name}' already exists. Use 'state {name}' to check it.")
        return 1
    # Create app directory
    app_dir = USER_APPS_DIR + '/' + name
    node = {'type': 'directory', 'contents': {'main.rub': {'type': 'file'}}}
    user_apps[name] = node
    kernel[app_dir] = node
    # Seed main.rub
    rub_path = app_dir + '/main.rub'
    directory_contents[rub_path] = {
        'type': 'txt',
        'content': _APP_TEMPLATE,
        'created_in': app_dir,
    }
    save_file_contents()
    save_filesystem()
    print(f"Created app '{name}' at {app_dir}/main.rub")
    print(f"  Edit: cd {app_dir} && edit main.rub")
    print(f"  Check: state {name}")
    print(f"  Run:   {name}")
    return 0

def state_command(args):
    """state <name>  — parse-check a user app without running it."""
    if not args:
        apps = _list_user_apps()
        if not apps:
            print("No user apps yet. Use 'create -cli <name>' to make one.")
        else:
            print("User apps:")
            for a in apps:
                src = _get_app_source(a)
                status = 'OK' if src is not None else 'missing main.rub'
                print(f"  {a:<20} {status}")
        return 0
    name = args.strip()
    src = _get_app_source(name)
    if src is None:
        print(f"App '{name}' not found. Use 'create -cli {name}' to create it.")
        return 1
    rubus = _get_rubus()
    errors = rubus.check(src)
    if not errors:
        lines = src.count('\n') + 1
        print(f"[{name}] OK — {lines} lines, no errors.")
    else:
        print(f"[{name}] {len(errors)} error(s) found:")
        for e in errors:
            print(e)
    return 0 if not errors else 1

def _run_user_app(name):
    """Run a user-created RubOS app by name."""
    src = _get_app_source(name)
    if src is None:
        return None  # not a user app
    rubus = _get_rubus()
    ctx = rubus.PYDOSContext(
        directory_contents, kernel, current_directory,
        join_path, save_file_contents, save_filesystem
    )
    return rubus.run(src, ctx)

def _hash_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

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

def _read_password_masked(prompt):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    entered = []
    while True:
        ch = readchar.readchar()
        if ch in ('\r', '\n'):
            print()
            break
        elif ch in ('\x7f', '\x08'):
            if entered:
                entered.pop()
                clear = ' ' * (len(prompt) + PASS_SLOTS + 2)
                sys.stdout.write(f"\r{clear}\r{prompt}{'*' * len(entered)}")
                sys.stdout.flush()
        elif len(entered) < PASS_SLOTS:
            entered.append(ch)
            sys.stdout.write('*')
            sys.stdout.flush()
    return ''.join(entered)

def _lockscreen_prompt(message=None):
    clear_terminal()
    print(PY_DOS)
    if message:
        print(f"{'Incorrect password!':^80}\n")
    pad   = ' ' * 30
    blank = '_' * PASS_SLOTS
    sys.stdout.write(f"{pad}Password [{blank}]")
    sys.stdout.flush()
    entered = []
    while True:
        ch = readchar.readchar()
        if ch in ('\r', '\n'):
            break
        elif ch in ('\x7f', '\x08'):
            if entered:
                entered.pop()
                display = '*' * len(entered) + '_' * (PASS_SLOTS - len(entered))
                sys.stdout.write(f"\r{pad}Password [{display}]")
                sys.stdout.flush()
        elif len(entered) < PASS_SLOTS:
            entered.append(ch)
            display = '*' * len(entered) + '_' * (PASS_SLOTS - len(entered))
            sys.stdout.write(f"\r{pad}Password [{display}]")
            sys.stdout.flush()
    print()
    return ''.join(entered)

PASS_SLOTS = 20  #Changwe for limit 

def display_lockscreen():
    auth = _load_auth()
    if auth is None or not auth.get('hash'):
        return

    message = None
    while True:
        raw = _lockscreen_prompt(message=message)
        if _hash_password(raw) == auth.get('hash'):
            return
        message = True   # triggers "Incorrect Password!" on next iteration

def pass_command(args):
    if not args:
        print("Usage:")
        print("  pass set              - set a new password")
        print("  pass change           - change existing password")
        print("  pass rm               - remove password protection")
        return

    parts = args.split()
    sub   = parts[0].lower()

    if sub == 'set':
        if _load_auth() is not None:
            print("A password is already set. Use 'pass change' to update it.")
            return
        raw     = _read_password_masked(f"New password (max {PASS_SLOTS} chars): ")
        confirm = _read_password_masked("Confirm password: ")
        if not raw:
            print("Password cannot be empty.")
            return
        if raw != confirm:
            print("Passwords do not match. Password not set.")
            return
        _save_auth({'hash': _hash_password(raw)})
        print("Password set.")

    elif sub == 'change':
        auth = _load_auth()
        if auth is None:
            print("No password is set. Use 'pass set' first.")
            return
        old_raw = _read_password_masked("Current password: ")
        if _hash_password(old_raw) != auth.get('hash'):
            print("Incorrect current password.")
            return
        new_raw = _read_password_masked("New password (max 8 chars): ")
        confirm = _read_password_masked("Confirm new password: ")
        if not new_raw:
            print("Password cannot be empty.")
            return
        if new_raw != confirm:
            print("Passwords do not match. Password not changed.")
            return
        _save_auth({'hash': _hash_password(new_raw)})
        print("Password changed.")

    elif sub == 'rm':
        auth = _load_auth()
        if auth is None:
            print("No password is set.")
            return
        confirm_raw = _read_password_masked("Enter current password to confirm removal: ")
        if _hash_password(confirm_raw) != auth.get('hash'):
            print("Incorrect password. Aborted.")
            return
        ans = input("Remove password protection? [y/N]: ").strip().lower()
        if ans == 'y':
            _delete_auth()
            print("Password removed.")
        else:
            print("Aborted.")

    else:
        print(f"Unknown subcommand '{sub}'. Use: pass set / pass change / pass rm")

def update_time_display():
    global clock_running, _editor_open
    last_minute = None
    while clock_running:
        if not _editor_open:
            current_minute = datetime.now().strftime("%H:%M")
            if current_minute != last_minute:
                last_minute = current_minute
                sys.stdout.write("\033[s")
                sys.stdout.write("\033[4;1H")
                sys.stdout.write(f"Time: [{current_minute}]" + " " * 20)
                sys.stdout.write("\033[u")
                sys.stdout.flush()
        time.sleep(1)

def start_clock():
    global clock_running, clock_thread
    clock_running = True
    clock_thread = threading.Thread(target=update_time_display, daemon=True)
    clock_thread.start()

def stop_clock():
    global clock_running
    clock_running = False

    
def clear_terminal():
    os.system('cls' if sys.platform.startswith('win') else 'clear')



def display_loading_screen():
    clear_terminal()
    print(PY_DOS)
    print("\nLoading filesystem...")
    print("="*32)
    clear_terminal()
    bar_width = 40
    for i in range(bar_width + 1):   
        progress = "#" * i + ":" * (bar_width - i)
        print(f"\r[{progress}]", end="", flush=True)
        time.sleep(0.05)
    
    print("\n")
    load_filesystem()
    time.sleep(0.5)
    display_lockscreen()

def display_home():
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version Beta]")
    print("ENTER 'help' TO GET STARTED.")
    get_battery_status()
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"Time: {current_time}")
    start_clock()
    

def get_current_path():
    return current_directory.replace('/', '\\') if current_directory != '/' else '\\'

def check_input():
    return input(f"PY DOS {get_current_path()}> ")

def normalize_path(path):
    if path.startswith('/'):
        parts = path.strip('/').split('/')
    else:
        parts = current_directory.strip('/').split('/')
        if current_directory == '/':
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

def join_path(base, name):
    if base == '/':
        return '/' + name
    return base + '/' + name

def ensure_saved_folder():
    Path(SAVED_FOLDER).mkdir(exist_ok=True)

def save_file_contents():
    try:
        ensure_saved_folder()
        file_path = Path(SAVED_FOLDER) / 'file_contents.bin'
        with open(file_path, 'wb') as f:
            pickle.dump(directory_contents, f)
    except Exception as e:
        print(f"Error saving file contents: {e}")

def load_file_contents():
    global directory_contents
    try:
        file_path = Path(SAVED_FOLDER) / 'file_contents.bin'
        if file_path.exists():
            with open(file_path, 'rb') as f:
                directory_contents = pickle.load(f)
        else:
            directory_contents = {}
    except Exception as e:
        print(f"Error loading file contents: {e}")
        directory_contents = {}

def save_filesystem():
    try:
        save_data = {'kernel': kernel, 'current_directory': current_directory}
        
        history = []
        try:
            for i in range(readline.get_current_history_length()):
                history.append(readline.get_history_item(i + 1))
            save_data['command_history'] = history[-10:]
        except:
            save_data['command_history'] = []
            
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        save_file_contents()
        print("State : NS [N/E]")
    except Exception as e:
        print(f"Error saving filesystem: {e}")
        
def _reconcile_kernel_flat_index():
    """Rebuild kernel's flat path-keyed entries so each one IS the same
    object as its corresponding node in the nested 'contents' tree (not a
    separate copy). Needed because JSON can't preserve object identity, so
    save_filesystem()/load_filesystem() silently re-splits the two views
    into disconnected dicts on every round-trip otherwise - which is what
    made mktf/mkef-created files (and 'ls'-walked directories generally)
    go invisible. cd/ls/dir only ever read the nested tree; mktf/mkef/rmdir
    only ever write through the flat kernel[path] keys - this keeps both
    looking at the same data."""
    def walk(node, path):
        kernel[path] = node
        for name, child in node.get('contents', {}).items():
            if child.get('type') == 'directory':
                child_path = path.rstrip('/') + '/' + name if path != '/' else '/' + name
                walk(child, child_path)
    walk(kernel['/'], '/')

def load_filesystem():
    global kernel, current_directory
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            kernel = save_data.get('kernel', kernel)
            current_directory = save_data.get('current_directory', '/')
            load_file_contents()
            print("Filesystem loaded from previous session.")
        else:
            print("State: CS [N/E]")
    except Exception as e:
        print(f"State: SS [E/E]  ----> CS")
    _reconcile_kernel_flat_index()
    _seed_lynx_app()
    _seed_mutiny_app()
    _ensure_user_apps_dir()

def get_battery_status():
    battery = psutil.sensors_battery()
    if battery is None:
        print("Battery: [################] 100% ⚡ | Desktop")
        return

    percent = int(battery.percent)
    filled = int(percent / 5)
    empty = 20 - filled
    bar = "#" * filled + ":" * empty
    
    icon = "⚡" if battery.power_plugged else ""
    
    if battery.secsleft == psutil.POWER_TIME_UNLIMITED:
        time_str = "Charging"
    elif battery.secsleft == psutil.POWER_TIME_UNKNOWN:
        time_str = "Unknown"
    else:
        minutes, seconds = divmod(battery.secsleft, 60)
        hours, minutes = divmod(minutes, 60)
        time_str = f"{int(hours)}h {int(minutes)}m"
    
    print(f"Battery: [{bar}] {percent}% {icon}")
    print(f"Time Left: {time_str}")

def get_cpu_stats():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_count = psutil.cpu_count()
    return cpu_percent, cpu_count

def get_memory_stats():
    memory = psutil.virtual_memory()
    return memory.percent, memory.used, memory.total

def get_disk_stats():
    disk = psutil.disk_usage('/')
    return disk.percent, disk.used, disk.total

def get_gpu_stats():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            return [(gpu.name, gpu.load * 100, gpu.memoryUsed, gpu.memoryTotal) for gpu in gpus]
    except:
        pass
    return None

def format_bytes(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f}PB"

        
_PM_RELAY = {
    'cachyos':      'pacman',
    'arch':         'pacman',
    'manjaro':      'pacman',
    'endeavouros':  'pacman',
    'artix':        'pacman',
    'garuda':       'pacman',
    'ubuntu':       'apt',
    'debian':       'apt',
    'linuxmint':    'apt',
    'pop':          'apt',
    'elementary':   'apt',
    'kali':         'apt',
    'raspbian':     'apt',
    'fedora':       'dnf',
    'rhel':         'dnf',
    'centos':       'dnf',
    'rocky':        'dnf',
    'alma':         'dnf',
    'opensuse':     'zypper',
    'suse':         'zypper',
    'alpine':       'apk',
    'macos':        'brew',
    'windows':      None,
}

_PM_CMD = {
    'pacman': 'pacman',
    'apt':    'apt',
    'dnf':    'dnf',
    'zypper': 'zypper',
    'apk':    'apk',
    'brew':   'brew',
}

def _detect_os_info():
    global _sys_profile
    if _sys_profile:
        return _sys_profile.get('os_info', {})

    os_info = {
        'system':      platform.system(),
        'release':     platform.release(),
        'distro':      'unknown',
        'distro_name': 'Unknown',
    }

    if os_info['system'] == 'Linux':
        try:
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('ID='):
                        os_info['distro'] = line.split('=',1)[1].strip().strip('"').lower()
                    elif line.startswith('NAME='):
                        os_info['distro_name'] = line.split('=',1)[1].strip().strip('"')
        except FileNotFoundError:
            for path, distro in (
                ('/etc/arch-release',   'arch'),
                ('/etc/debian_version', 'debian'),
                ('/etc/redhat-release', 'rhel'),
                ('/etc/SuSE-release',   'opensuse'),
                ('/etc/alpine-release', 'alpine'),
            ):
                if os.path.exists(path):
                    os_info['distro'] = distro
                    break
    elif os_info['system'] == 'Darwin':
        os_info['distro'] = 'macos'
        os_info['distro_name'] = 'macOS'
    elif os_info['system'] == 'Windows':
        os_info['distro'] = 'windows'
        os_info['distro_name'] = 'Windows'

    return os_info


def _detect_package_manager():
    global _sys_profile
    if _sys_profile:
        return _sys_profile.get('pm_info', {})

    os_info = _detect_os_info()
    distro  = os_info.get('distro', 'unknown')

    # Relay: known distro → definitive PM
    pm_name = None
    for key in _PM_RELAY:
        if key in distro:
            pm_name = _PM_RELAY[key]
            break

    # Fallback: scan PATH
    available = {}
    if pm_name and shutil.which(_PM_CMD.get(pm_name, '')):
        available[pm_name] = _PM_CMD[pm_name]
    else:
        for name, cmd in _PM_CMD.items():
            if cmd and shutil.which(cmd):
                available[name] = cmd

    return {'os_info': os_info, 'package_managers': available}
def _is_package_installed(package_name, use_pip=True):
    """Check if a package is already installed."""
    try:
        if use_pip:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        return None
    return False

def _install_via_pip(package_name):
    """Install package via pip."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--quiet', '--upgrade', package_name],
            capture_output=True, text=True, timeout=120
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except subprocess.TimeoutExpired:
        return False, "Installation timed out (>120s)"
    except Exception as e:
        return False, str(e)

def _install_via_system_pm(package_name, pm_name, pm_cmd):
    """Install package via system package manager."""
    try:
        # Map pip package names to common system package names
        system_pkg_name = package_name.lower().replace('_', '-').replace('.', '-')
        
        print(f"\n[*] Attempting system installation via {pm_name}...")
        
        if pm_name == 'apt':
            cmd = ['sudo', pm_cmd, 'install', '-y', system_pkg_name]
        elif pm_name == 'pacman':
            cmd = ['sudo', pm_cmd, '-S', '--noconfirm', system_pkg_name]
        elif pm_name == 'dnf':
            cmd = ['sudo', pm_cmd, 'install', '-y', system_pkg_name]
        elif pm_name == 'zypper':
            cmd = ['sudo', pm_cmd, 'install', '-y', system_pkg_name]
        elif pm_name == 'brew':
            cmd = [pm_cmd, 'install', system_pkg_name]
        elif pm_name == 'apk':
            cmd = ['sudo', pm_cmd, 'add', system_pkg_name]
        else:
            return False, f"Unknown package manager: {pm_name}"
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except subprocess.TimeoutExpired:
        return False, "Installation timed out (>120s)"
    except Exception as e:
        return False, str(e)

def install_command(args):
    """Enhanced install command with smart OS/distro and package manager detection."""
    if not args:
        print("Usage: install <package_name>")
        print("Supports: pip packages, system packages (auto-detected)")
        return
    
    package_name = args.strip()
    print(f"\n[*] Checking if '{package_name}' is already installed...")
    
    # Check pip first
    is_installed = _is_package_installed(package_name, use_pip=True)
    if is_installed:
        print(f"[✓] Package '{package_name}' is already installed via pip.")
        return
    elif is_installed is None:
        print(f"[!] Could not determine installation status (pip timeout)")
    
    # Try pip installation first
    print(f"\n[*] Installing '{package_name}' via pip...")
    success, error = _install_via_pip(package_name)
    
    if success:
        print(f"[✓] Successfully installed '{package_name}' via pip!")
        return
    else:
        print(f"[✗] pip installation failed: {error}")
    
    # Fallback to system package manager
    detection = _detect_package_manager()
    os_info = detection['os_info']
    available_pms = detection['package_managers']
    
    print(f"\n[*] Detected OS: {os_info['distro_name']} ({os_info['system']} {os_info['release']})")
    
    if available_pms:
        pm_list = ', '.join(available_pms.keys())
        print(f"[*] Detected system package managers: {pm_list}")
        
        # Try each available PM
        for pm_name, pm_cmd in available_pms.items():
            success, error = _install_via_system_pm(package_name, pm_name, pm_cmd)
            if success:
                print(f"[✓] Successfully installed '{package_name}' via {pm_name}!")
                return
            else:
                print(f"[✗] {pm_name} installation failed: {error}")
        
        print(f"\n[!] All installation methods failed.")
        print(f"    Package name mismatch? System packages may differ from pip names.")
        first_pm = list(available_pms.keys())[0]
        pm_cmd = available_pms[first_pm]
        print(f"    Try: sudo {pm_cmd} search {package_name.lower()}")
    else:
        print(f"\n[!] No system package manager detected.")
        if os_info['system'] == 'Windows':
            print(f"    Windows systems typically use winget, chocolatey, or scoop.")
            print(f"    For Python packages, pip is recommended.")
        elif os_info['system'] == 'Darwin':
            print(f"    macOS: brew not found. Install from: https://brew.sh/")
        else:
            print(f"    Linux distro: {os_info['distro_name']}")
            print(f"    Supported PMs: apt, pacman, dnf, zypper, apk")
            print(f"    Your package manager may not be in PATH or not installed.")

def uninstall_command(args):
    """Enhanced uninstall command."""
    if not args:
        print("Usage: uninstall <package_name>")
        return
    
    package_name = args.strip()
    print(f"\n[*] Uninstalling '{package_name}'...\n")
    
    # Try pip first
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'uninstall', '-y', package_name],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            print(f"[✓] Successfully uninstalled '{package_name}' via pip!")
            return
        else:
            print(f"[!] pip uninstall reported issues:")
            print(result.stdout if result.stdout else result.stderr)
    except subprocess.TimeoutExpired:
        print(f"[✗] Uninstall timed out (>60s)")
    except Exception as e:
        print(f"[✗] Error: {e}")

def cache_sudo():
    global _sudo_cached, _sys_profile
    if _sudo_cached or _sys_profile.get('sudo_cached'):
        _sudo_cached = True
        return True

    print("\n[Sudo Caching]")
    resp = input("Cache sudo credentials for this session? (y/N): ").strip().lower()
    if resp not in ('y', 'yes'):
        print("Skipping sudo cache.")
        return False

    if subprocess.run(['sudo', '-v']).returncode != 0:
        print("[!] Failed to authenticate sudo.")
        return False

    def _keepalive():
        while True:
            time.sleep(50)
            try:
                if subprocess.run(['sudo', '-n', 'true'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL).returncode != 0:
                    break
            except OSError:
                break

    threading.Thread(target=_keepalive, daemon=True).start()
    _sudo_cached = True
    _sys_profile['sudo_cached'] = True
    _persist_sys_profile()
    print("[✓] Sudo credentials cached.")
    return True

def _persist_sys_profile():
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE) as f:
                data = json.load(f)
        else:
            data = {}
        data['sys_profile'] = _sys_profile
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def _load_sys_profile():
    global _sys_profile
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE) as f:
                data = json.load(f)
            _sys_profile = data.get('sys_profile', {})
    except Exception:
        _sys_profile = {}

    if not _sys_profile.get('os_info'):
        os_info = _detect_os_info()
        pm_info = _detect_package_manager()
        _sys_profile['os_info'] = os_info
        _sys_profile['pm_info'] = pm_info
        _persist_sys_profile()

def cd_command(args):
    global current_directory
    if not args:
        print(current_directory)
        return
    
    if args == '..':
        if current_directory == '/':
            return
        parts = current_directory.rstrip('/').split('/')
        current_directory = '/'.join(parts[:-1]) or '/'
        return
    
    if args == '/':
        current_directory = '/'
        return
    
    if args.startswith('/'):
        target_path = args
    else:
        target_path = current_directory.rstrip('/') + '/' + args if current_directory != '/' else '/' + args
    
    target_path = target_path.rstrip('/')
    if target_path == '':
        target_path = '/'
    
    parts = target_path.strip('/').split('/') if target_path != '/' else []
    current_node = kernel['/']
    
    for part in parts:
        if 'contents' in current_node and part in current_node['contents'] and current_node['contents'][part]['type'] == 'directory':
            current_node = current_node['contents'][part]
        else:
            print(f"Directory not found: {args}")
            return
    
    current_directory = target_path
    save_filesystem()

def mkdir_command(args):
    if not args:
        print("Usage: mkdir <directory_name>")
        return
        
    dirname = args
    new_path = normalize_path(dirname)
    
    if new_path in kernel:
        print(f"Directory '{dirname}' already exists")
        return
    
    parent_path = '/'.join(new_path.split('/')[:-1]) or '/'
    
    if parent_path == '/':
        parent_node = kernel['/']
    else:
        parts = parent_path.strip('/').split('/')
        parent_node = kernel['/']
        for part in parts:
            if 'contents' in parent_node and part in parent_node['contents']:
                parent_node = parent_node['contents'][part]
            else:
                print("Parent directory not found.")
                return
    
    dir_name_only = new_path.split('/')[-1]
    new_node = {'type': 'directory', 'contents': {}}
    kernel[new_path] = new_node
    parent_node['contents'][dir_name_only] = new_node
    save_filesystem()
    print(f"Directory '{dirname}' created")

def rmdir_command(args):
    if not args:
        print("Usage: rmdir <directory_name>")
        return
    
    dirname = args
    target_path = normalize_path(dirname)
    
    if target_path not in kernel or kernel[target_path]['type'] != 'directory':
        print("Directory not found")
        return
    
    if kernel[target_path]['contents']:
        print("Directory is not empty")
        return
    
    del kernel[target_path]
    parent_path = '/'.join(target_path.split('/')[:-1]) or '/'
    if parent_path in kernel:
        dir_name_only = target_path.split('/')[-1]
        if dir_name_only in kernel[parent_path]['contents']:
            del kernel[parent_path]['contents'][dir_name_only]
    save_filesystem()

def _get_dir_node():
    if current_directory == '/':
        return kernel['/']
    node = kernel['/']
    for part in current_directory.strip('/').split('/'):
        if 'contents' in node and part in node['contents']:
            node = node['contents'][part]
        else:
            return None
    return node

def _glob_match(names, pattern):
    """Match names in current dir against a glob pattern."""
    matched = [n for n in names if fnmatch.fnmatch(n, pattern)]
    return matched  # empty = no match

def ls_command(args=None):
    global _piped_input
    long_fmt = False
    show_hidden = False
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

    node = _get_dir_node()
    if node is None:
        print("Current directory not found.")
        return 1

    contents = node.get('contents', {})
    names = [n for n in contents if show_hidden or not n.startswith('.')]

    if pattern:
        matched = _glob_match(names, pattern)
        if not matched:
            print(f"ls: no match: {pattern}")
            return 1
        names = matched

    if not names:
        print("Directory is empty")
        return 0

    if current_directory != '/':
        print(f"Directory of {current_directory}\n")

    for name in sorted(names):
        item = contents[name]
        if long_fmt:
            fpath = join_path(current_directory, name)
            ftype = 'DIR ' if item['type'] == 'directory' else 'FILE'
            size_str = ''
            if fpath in directory_contents:
                content = directory_contents[fpath].get('content', '')
                size_str = f"{len(content):>8} B"
            else:
                size_str = '       -  '
            created = directory_contents.get(fpath, {}).get('created_in', current_directory)
            print(f"{ftype}  {size_str}  {name}")
        else:
            if item['type'] == 'directory':
                print(f"<DIR>          {name}")
            else:
                print(f"<FILE>         {name}")
    return 0

def grep_command(args):
    """grep <pattern> [file] — filter lines. Reads piped input if no file given."""
    global _piped_input
    if not args:
        print("Usage: grep <pattern> [file]")
        return 1
    try:
        tokens = shlex.split(args)
    except ValueError:
        tokens = args.split()

    flags_here = [t for t in tokens if t.startswith('-')]
    rest = [t for t in tokens if not t.startswith('-')]
    ignore_case = '-i' in flags_here
    invert = '-v' in flags_here

    if not rest:
        print("grep: missing pattern")
        return 1

    pattern = rest[0]
    filename = rest[1] if len(rest) > 1 else None

    if filename:
        fpath = join_path(current_directory, filename)
        if fpath not in directory_contents:
            print(f"grep: {filename}: No such file")
            return 1
        text = directory_contents[fpath].get('content', '')
    elif _piped_input is not None:
        text = _piped_input
    else:
        print("grep: no input (pipe something or give a filename)")
        return 1

    found = False
    for line in text.splitlines():
        hay = line.lower() if ignore_case else line
        pat = pattern.lower() if ignore_case else pattern
        match = fnmatch.fnmatch(hay, f'*{pat}*')
        if match != invert:
            print(line)
            found = True
    return 0 if found else 1

def rem_command(args):
    if not args or " to " not in args:
        print("Usage: rem <originalname> to <newname>")
        return
    
    parts = args.split(" to ")
    file_name = parts[0].strip()
    new_file_name = parts[1].strip()
    
    file_path = join_path(current_directory, file_name)
    new_file_path = join_path(current_directory, new_file_name)

    if file_path not in directory_contents:
        print("File not found.")
        return

    if new_file_path in directory_contents:
        print("File already exists.")
        return
    
    directory_contents[new_file_path] = directory_contents[file_path]
    del directory_contents[file_path]
    del kernel[current_directory]['contents'][file_name]
    kernel[current_directory]['contents'][new_file_name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()
    print(f"'{file_name}' renamed to '{new_file_name}' successfully.")

def mktf_command(args):
    global _editor_open
    _editor_open = True
    os.system(f"nvim {temp_path}")
    _editor_open = False
    if not args:
        print("Usage: mktf <filename>")
        return
    
    file_name = args
    file_path = join_path(current_directory, file_name)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = f.name
    
  
    
    print("\nCreating text file...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save and exit | ':q!' to exit without saving")
    input("Press ENTER to continue...")
    
    if sys.platform.startswith('win'):
        os.system(f"notepad {temp_path}")
    else:
        os.system(f"nvim {temp_path}")
    
 
    
    with open(temp_path, 'r') as f:
        content = f.read()
    
    directory_contents[file_path] = {
        'type': 'txt',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
    
    os.unlink(temp_path)
    save_file_contents()
    save_filesystem()
    print(f"Text file '{file_name}' created successfully.")

def mkef_command(args):
    global _editor_open
    _editor_open = True
    os.system(f"nvim {temp_path}")
    _editor_open = False
    if not args:
        print("Usage: mkef <filename>")
        return
    
    file_name = args
    file_path = join_path(current_directory, file_name)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_path = f.name
    


    
    print("\nCreating executable file...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save and exit | ':q!' to exit without saving")
    input("Press ENTER to continue...")
    
    if sys.platform.startswith('win'):
        os.system(f"notepad {temp_path}")
    else:
        os.system(f"nvim {temp_path}")
    
 
    
    with open(temp_path, 'r') as f:
        content = f.read()
    
    directory_contents[file_path] = {
        'type': 'exe',
        'content': content,
        'created_in': current_directory
    }
    
    if current_directory in kernel:
        kernel[current_directory]['contents'][file_name] = {'type': 'file'}
    
    os.unlink(temp_path)
    save_file_contents()
    save_filesystem()
    print(f"Executable file '{file_name}' created successfully.")

def rm_command_ex(args, recursive=False, force=False):
    if not args:
        if not force:
            print("Usage: rm [-r] [-f] <name>")
        return

    if args == 'all':
        rm_command(args)
        return

    target_path = join_path(current_directory, args)

    # Try as file first
    if target_path in directory_contents:
        del directory_contents[target_path]
        if current_directory in kernel and args in kernel[current_directory]['contents']:
            del kernel[current_directory]['contents'][args]
        save_file_contents()
        save_filesystem()
        print(f"File '{args}' deleted.")
        return

    # Try as directory with -r
    if recursive and target_path in kernel and kernel[target_path]['type'] == 'directory':
        def _rm_dir(path):
            for name, item in list(kernel[path]['contents'].items()):
                child_path = join_path(path, name)
                if item['type'] == 'directory':
                    _rm_dir(child_path)
                else:
                    directory_contents.pop(child_path, None)
            del kernel[path]
        parent_path = '/'.join(target_path.split('/')[:-1]) or '/'
        dir_name = target_path.split('/')[-1]
        _rm_dir(target_path)
        if parent_path in kernel:
            kernel[parent_path]['contents'].pop(dir_name, None)
        save_file_contents()
        save_filesystem()
        print(f"Directory '{args}' removed.")
        return

    if not force:
        if target_path in kernel:
            print(f"'{args}' is a directory. Use rm -r to remove it.")
        else:
            print("File not found.")

def rm_command(args):
    rm_command_ex(args, recursive=False, force=False)



def copy_command(args):    
    if not args or ' to ' not in args:
        print("Usage: copy <filename> to <directory>")
        return
    
    parts = args.split(' to ')
    file_name = parts[0].strip()
    target_path = parts[1].strip()
    source_path = join_path(current_directory, file_name)

    if source_path not in directory_contents:
        print("Source file not found")
        return

    target_path = normalize_path(target_path)
    if target_path not in kernel:
        print("Target directory not found")
        return

    content = directory_contents[source_path]
    target_file_path = join_path(target_path, file_name)
    directory_contents[target_file_path] = {
        'type': directory_contents[source_path]['type'],
        'content': content['content'],
        'created_in': target_path
    }
    
    kernel[target_path]['contents'][file_name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()
    print(f"File '{file_name}' copied to {target_path} successfully.")

def move_command(args):
    if not args or ' to ' not in args:
        print("Usage: move <filename> to <directory>")
        return
    
    parts = args.split(' to ')
    file_name = parts[0].strip()
    target_path = parts[1].strip()
    source_path = join_path(current_directory, file_name)

    if source_path not in directory_contents:
        print("Source file not found")
        return

    target_path = normalize_path(target_path)
    if target_path not in kernel:
        print("Target directory not found")
        return

    content = directory_contents[source_path]  
    target_file_path = join_path(target_path, file_name)
    
    directory_contents[target_file_path] = {
        'type': directory_contents[source_path]['type'],
        'content': content['content'],
        'created_in': target_path
    }
    del directory_contents[source_path]
    del kernel[current_directory]['contents'][file_name]
    kernel[target_path]['contents'][file_name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()
    print(f"File '{file_name}' moved to {target_path} successfully.")

def edit_command(args):
    global _editor_open
    _editor_open = True
    os.system(f"nvim {temp_path}")
    _editor_open = False
    if not args:
        print("Usage: edit <filename>")
        return
    
    file_path = join_path(current_directory, args)
    if file_path not in directory_contents:
        print("File not found.")
        return
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(directory_contents[file_path]['content'])
        temp_path = f.name
    
    
    
    print("\nOpening editor...")
    print("Press 'i' to start typing | 'Esc' to stop | ':wq' to save and exit | ':q!' to exit without saving")
    input("Press ENTER to continue...")
    
    if sys.platform.startswith('win'):
        os.system(f"notepad {temp_path}")
    else:
        os.system(f"nvim {temp_path}")
 
    
    with open(temp_path, 'r') as f:
        directory_contents[file_path]['content'] = f.read()
    
    os.unlink(temp_path)
    save_file_contents()
    save_filesystem()
    print(f"Saved '{args}'")

def vwtf_command(args):
    if not args:
        print("Usage: vwtf <filename>")
        return
        
    file_path = join_path(current_directory, args)
    if file_path in directory_contents:
        print(directory_contents[file_path]['content'])
    else:
        print("File not found.")

def create_module_from_pydos_file(module_name, file_path):
    if file_path not in directory_contents:
        return None
    
    code = directory_contents[file_path]['content']
    module = types.ModuleType(module_name)
    module.__file__ = file_path
    module.__name__ = module_name
    
    try:
        exec(code, module.__dict__)
        return module
    except Exception as e:
        print(f"Error loading module {module_name}: {e}")
        return None

def run_command(args):
    if not args:
        print("Usage: run <filename> [args]")
        return
    
    parts = args.split(None, 1)
    file_name = parts[0]
    run_args = parts[1] if len(parts) > 1 else ''
    file_path = f"{current_directory}/{file_name}".replace('//', '/')
    
    # If file not found in current directory, check standard app directories
    if file_path not in directory_contents:
        app_search_paths = [
            f"/Apps/Utilities/Mutiny/{file_name}",
            f"/Apps/Utilities/Lynx/{file_name}"
        ]
        for alt_path in app_search_paths:
            if alt_path in directory_contents:
                file_path = alt_path
                break
        else:
            print(f"File '{file_name}' not found.")
            return
    
    if directory_contents[file_path]['type'] != 'exe':
        print(f"'{file_name}' is not an executable file.")
        return
    
    code = directory_contents[file_path]['content']
    
    exec_globals = {
        '__builtins__': __builtins__,
        '__name__': '__main__',
        '__file__': file_path,
        '_pydos_run_args_': run_args,
    }
    
    temp_dir = tempfile.mkdtemp()
    original_path = sys.path.copy()
    sys.path.insert(0, temp_dir)
    
    try:
        for file_key in directory_contents:
            if directory_contents[file_key]['type'] == 'exe' and file_key.endswith('.py'):
                parts = file_key.strip('/').split('/')
                rel_path = '/'.join(parts)
                temp_file = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(temp_file), exist_ok=True)
                with open(temp_file, 'w') as f:
                    f.write(directory_contents[file_key]['content'])
        
        exec(code, exec_globals)
        
    except Exception as e:
        print(f"Error executing {file_name}: {e}")
    finally:
        sys.path = original_path
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def help_command(args=None):
    print("""

    =================================================
    [AVAILABLE COMMANDS:                            ]
    |  ---------- directory management -------------|
    |cd        - changes directory                  |
    |mkdir     - creates a directory                |
    |rmdir     - removes a directory                |
    |ls        - lists directory contents           |
    |  --------- file management -------------------|
    |mktf      - creates text files                 |
    |mkef      - creates executable files           |
    |rm        - removes files                      |
    |run       - runs executable files              |
    |vwtf      - shows file contents                |
    |copy      - copies files to another directory  |
    |move      - moves files to another directory   |
    |rem       - renames files                      |
    |edit      - edits existing files               |
    |   --------- system commands ------------------|
    |quit      - exits and saves                    |
    |sysinfo   - detailed system information        |
    |format    - resets filesystem                  |
    |clear     - clears terminal                    |
    |reboot    - reboots system                     |
    |  ---------- package manager ------------------|
    |install   - installs  packages                 |
    |uninstall - uninstalls packages                |
    |packages  - list installed pip packages        |
    |  -------------- security -------------------- |
    |pass set  - set a boot password                |
    |pass change - change existing password         |
    |pass rm   - remove password protection         |
    |  -------------- web browser ----------------- |
    |run web   - launch Lynx browser                |
    |            run web [url]  to open a URL       |
    |------------ mesh chat (mutiny) -------------- |
    |run setup - one-time mesh network setup        |
    |run community - host or join a mesh chat       |
    =================================================

    """)

def format_command():
    global kernel, current_directory, directory_contents, _sys_profile, _sudo_cached

    # Wipe virtual FS
    kernel = {
        '/': {
            'type': 'directory',
            'contents': {
                'bin': {'type': 'directory', 'contents': {}},
                'usr': {'type': 'directory', 'contents': {}},
                'tmp': {'type': 'directory', 'contents': {}},
            }
        }
    }
    current_directory = '/'
    directory_contents = {}
    _sys_profile = {}
    _sudo_cached = False

    try:
        readline.clear_history()
    except Exception:
        pass

    # Delete filesystem.json
    if os.path.exists(FILESYSTEM_FILE):
        os.remove(FILESYSTEM_FILE)

    # Delete saved/ folder
    if os.path.exists(SAVED_FOLDER):
        shutil.rmtree(SAVED_FOLDER)

    # Delete all __pycache__ dirs relative to the package
    pkg_root = os.path.dirname(os.path.abspath(__file__))
    for dirpath, dirnames, _ in os.walk(pkg_root):
        for d in dirnames:
            if d == '__pycache__':
                shutil.rmtree(os.path.join(dirpath, d))

    print("Filesystem formatted and cache cleared.")
def clear_command():
    clear_terminal()
    display_home()

def _sysinfo_logo(distro):
    """Return (logo_lines, color_code) for the detected distro."""
    logos = {
        'cachyos': (
            "\033[1;36m",  # cyan
            [
                "      ___      ",
                "    /  __  \\   ",
                "   /  /  \\  \\  ",
                "  /  / C  /  / ",
                " /___\\___/  /  ",
                "  \\________/   ",
                "   CachyOS     ",
            ]
        ),
        'arch': (
            "\033[1;36m",
            [
                "       /\\      ",
                "      /  \\     ",
                "     /\\   \\    ",
                "    /  __  \\   ",
                "   / /    \\ \\  ",
                "  /_/      \\_\\ ",
                "    Arch Linux ",
            ]
        ),
        'ubuntu': (
            "\033[1;33m",  # yellow
            [
                "   _____       ",
                "  /  __  \\     ",
                " |  /  \\  |    ",
                " |  \\__/  |    ",
                "  \\______/     ",
                "               ",
                "    Ubuntu     ",
            ]
        ),
        'debian': (
            "\033[1;31m",  # red
            [
                "   ______      ",
                "  /  __   \\    ",
                " /  /  )   |   ",
                "|  |  (    |   ",
                " \\  \\__)   /   ",
                "  \\______./    ",
                "    Debian     ",
            ]
        ),
        'fedora': (
            "\033[1;34m",  # blue
            [
                "   ______      ",
                "  /  ____\\     ",
                " /  /___       ",
                "|  |_____      ",
                " \\  \\_____|    ",
                "  \\______/     ",
                "    Fedora     ",
            ]
        ),
        'manjaro': (
            "\033[1;32m",  # green
            [
                " ___________   ",
                "|  _______  |  ",
                "| |       | |  ",
                "| |  MJR  | |  ",
                "| |_______| |  ",
                "|___________|  ",
                "   Manjaro     ",
            ]
        ),
    }
    distro_lower = distro.lower()
    for key in logos:
        if key in distro_lower:
            return logos[key]
    # generic penguin fallback
    return (
        "\033[1;37m",
        [
            "    .---.      ",
            "   /     \\     ",
            "  | () () |    ",
            "   \\  ^  /     ",
            "    |||||      ",
            "    |||||      ",
            "    Linux      ",
        ]
    )

def packages_command(args=None):
    print("\n[*] Installed packages:\n")
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--format=columns'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("[!] Could not retrieve package list.")

def _bar(percent, width=20):
    filled = int(width * percent / 100)
    return '[' + '#' * filled + '-' * (width - filled) + f'] {percent:.1f}%'

def sysinfo_command():
    clear_terminal()
    os_info = _detect_os_info()
    color, logo_lines = _sysinfo_logo(os_info['distro'])
    reset = "\033[0m"
    bold  = "\033[1m"

    cpu_percent, cpu_count = get_cpu_stats()
    mem_percent, mem_used, mem_total = get_memory_stats()
    disk_percent, disk_used, disk_total = get_disk_stats()
    battery = psutil.sensors_battery()
    gpu_stats = get_gpu_stats()

    # uptime
    try:
        uptime_s = int(time.time() - psutil.boot_time())
        h, rem = divmod(uptime_s, 3600)
        m = rem // 60
        uptime_str = f"{h}h {m}m"
    except Exception:
        uptime_str = "N/A"

    hostname = platform.node()
    user = os.environ.get('USER') or os.environ.get('USERNAME', 'user')

    info_lines = [
        f"{bold}{color}{user}@{hostname}{reset}",
        "─" * 28,
        f"{bold}OS      {reset} {os_info['distro_name']} {os_info['release']}",
        f"{bold}Arch    {reset} {platform.machine()}",
        f"{bold}Python  {reset} {sys.version.split()[0]}",
        f"{bold}Uptime  {reset} {uptime_str}",
        f"{bold}Shell   {reset} PY DOS",
        "",
        f"{bold}CPU     {reset} {platform.processor() or 'N/A'}",
        f"{bold}Cores   {reset} {cpu_count}",
        f"{bold}CPU %   {reset} {_bar(cpu_percent)}",
        "",
        f"{bold}RAM     {reset} {format_bytes(mem_used)} / {format_bytes(mem_total)}",
        f"{bold}RAM %   {reset} {_bar(mem_percent)}",
        "",
        f"{bold}Disk    {reset} {format_bytes(disk_used)} / {format_bytes(disk_total)}",
        f"{bold}Disk %  {reset} {_bar(disk_percent)}",
    ]

    if battery:
        bat_status = "⚡ Charging" if battery.power_plugged else "🔋 Discharging"
        info_lines.append(f"{bold}Battery {reset} {battery.percent:.0f}% {bat_status}")

    if gpu_stats:
        for i, (name, load, mu, mt) in enumerate(gpu_stats):
            info_lines.append(f"{bold}GPU{i}    {reset} {name}")
            info_lines.append(f"{bold}GPU{i} % {reset} {_bar(load)}")

    # Print logo + info side by side
    logo_width = 16
    max_rows = max(len(logo_lines), len(info_lines))
    print()
    for i in range(max_rows):
        logo_part = f"{color}{logo_lines[i]}{reset}" if i < len(logo_lines) else ' ' * logo_width
        info_part = info_lines[i] if i < len(info_lines) else ''
        print(f"  {logo_part}   {info_part}")
    print()

def quit_command():
    print("\nSaving filesystem...")
    bar_width = 40
    for i in range(bar_width + 1):
        progress = "#" * i + ":" * (bar_width - i)
        print(f"\r[{progress}]", end="", flush=True)
        time.sleep(0.05)
    print("\n")
    save_filesystem()
    sys.exit()

def reboot_command():
    save_filesystem()
    print("Rebooting...")
    time.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

def _strip_flags(args, flags):
    """Remove known flags from args string, return (cleaned_args, found_flags)."""
    if not args:
        return args, set()
    parts = args.split()
    found = set()
    remaining = []
    for p in parts:
        if p in flags:
            found.add(p)
        else:
            remaining.append(p)
    return ' '.join(remaining) or None, found

def echo_command(args):
    if not args:
        print()
        return 0
    text = args.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        text = text[1:-1]
    text = _expand_vars(text)
    print(text)
    return 0

command_functions = {
    'cd': cd_command,
    'mkdir': mkdir_command,
    'md': mkdir_command,
    'rmdir': rmdir_command,
    'rd': rmdir_command,
    'mktf': mktf_command,
    'touch': mktf_command,
    'copy con': mktf_command,
    'echo': echo_command,
    'vwtf': vwtf_command,
    'cat': vwtf_command,
    'type': vwtf_command,
    'mkef': mkef_command,
    'run': run_command,
    'start': run_command,
    'python': run_command,
    'rm': rm_command,
    'del': rm_command,
    'copy': copy_command,
    'rem': rem_command,
    'move': move_command,
    'edit': edit_command,
    'install': install_command,
    'uninstall': uninstall_command,
    'pass': pass_command,
    'grep': grep_command,
    'create': create_command,
    'state': state_command,
}

no_args_command_functions = {
    'packages': packages_command,
    'pkgs': packages_command,
    'ls': ls_command,
    'dir': ls_command,
    'help': help_command,
    'clear': clear_command,
    'cls': clear_command,
    'sysinfo': sysinfo_command,
    'quit': quit_command,
    'format': format_command,
    'reboot': reboot_command,
}

def setup_readline():
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
            history = save_data.get('command_history', [])
            
            for command in history:
                readline.add_history(command)
                
    except Exception as e:
        pass
    
    if readline:
        readline.set_history_length(10)

def save_history():
    history = []
    for i in range(readline.get_current_history_length()):
        history.append(readline.get_history_item(i + 1))
    
    try:
        if os.path.exists(FILESYSTEM_FILE):
            with open(FILESYSTEM_FILE, 'r') as f:
                save_data = json.load(f)
        else:
            save_data = {'kernel': kernel, 'current_directory': current_directory}
        
        save_data['command_history'] = history[-10:]
        
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
    except Exception as e:
        pass

def save_on_exit():
    save_history()
    try:
        save_data = {'kernel': kernel, 'current_directory': current_directory}
        history = []
        try:
            for i in range(readline.get_current_history_length()):
                history.append(readline.get_history_item(i + 1))
            save_data['command_history'] = history[-10:]
        except:
            save_data['command_history'] = []
        with open(FILESYSTEM_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        save_file_contents()
    except:
        pass

atexit.register(save_on_exit)

# ─── Shell expansion helpers ──────────────────────────────────────────────────

def _expand_vars(s):
    """Expand ~ and $? and $VAR in a string."""
    s = s.replace('~', '/')
    s = s.replace('$?', str(_last_exit))
    for k, v in _shell_vars.items():
        s = s.replace(f'${k}', v).replace(f'${{{k}}}', v)
    return s

def _expand_globs_in_args(args_str):
    """Expand glob patterns in args against the current virtual directory."""
    if not args_str:
        return args_str
    try:
        tokens = shlex.split(args_str)
    except ValueError:
        tokens = args_str.split()
    node = _get_dir_node()
    names = list(node['contents'].keys()) if node else []
    result = []
    for tok in tokens:
        if any(c in tok for c in ('*', '?', '[')):
            matched = _glob_match(names, tok)
            result.extend(matched if matched else [tok])
        else:
            result.append(tok)
    return ' '.join(shlex.quote(t) if ' ' in t else t for t in result)

# ─── Redirection helpers ──────────────────────────────────────────────────────

_REDIRECT_OPS = ('2>&1', '&>', '>>', '2>', '>', '<')

def _write_vfile(name, content, append=False):
    fpath = join_path(current_directory, name)
    if append and fpath in directory_contents:
        content = directory_contents[fpath].get('content', '') + content
    directory_contents[fpath] = {'type': 'txt', 'content': content, 'created_in': current_directory}
    kernel[current_directory]['contents'][name] = {'type': 'file'}
    save_file_contents()
    save_filesystem()

def _read_vfile(name):
    fpath = join_path(current_directory, name)
    return directory_contents[fpath].get('content', '') if fpath in directory_contents else None

def _parse_redirects(cmd_str):
    redirects = []
    remaining = cmd_str
    for op in _REDIRECT_OPS:
        while op in remaining:
            idx = remaining.find(op)
            before = remaining[:idx]
            after  = remaining[idx + len(op):].lstrip()
            if op == '2>&1':
                redirects.append((op, None))
                remaining = before + after
                break
            target_parts = after.split(None, 1)
            if not target_parts:
                break
            target = target_parts[0]
            rest   = target_parts[1] if len(target_parts) > 1 else ''
            redirects.append((op, target))
            remaining = before + rest
            break
    return remaining.strip(), redirects

def _split_on_op(s, op):
    """Split string on operator, respecting single and double quotes."""
    parts = []
    current = []
    in_sq = in_dq = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == "'" and not in_dq: in_sq = not in_sq
        elif c == '"' and not in_sq: in_dq = not in_dq
        if not in_sq and not in_dq and s[i:i+len(op)] == op:
            parts.append(''.join(current))
            current = []
            i += len(op)
            continue
        current.append(c)
        i += 1
    parts.append(''.join(current))
    return parts

# ─── Command dispatcher ───────────────────────────────────────────────────────

def _dispatch_single(raw_cmd, stdin_data=None):
    global _piped_input, _last_exit
    _piped_input = stdin_data
    raw_cmd = raw_cmd.strip()
    if not raw_cmd or raw_cmd.startswith('#'): return 0
    if raw_cmd.startswith('sudo '):
        inner     = raw_cmd[5:].strip()
        inner_cmd = inner.split()[0].lower()
        if inner_cmd not in command_functions and inner_cmd not in no_args_command_functions:
            return subprocess.run(['sudo'] + shlex.split(inner)).returncode
    raw_cmd = _expand_vars(raw_cmd)
    try:
        parts = shlex.split(raw_cmd)
    except ValueError:
        parts = raw_cmd.split()
    if not parts: return 0
    command   = parts[0].lower()
    args_str  = _expand_globs_in_args(' '.join(parts[1:])) if len(parts) > 1 else None
    stripped_args, flags = _strip_flags(args_str,
        {'-r', '-f', '-rf', '-fr', '--force', '--recursive',
         '-v', '--verbose', '-n', '--dry-run', '-i', '--interactive'})
    if args_str and any(t in ('-h', '--help') for t in args_str.split()):
        help_text = {
            'rm':    'rm [-r] [-f] [-i] [-n] <name|pattern>',
            'ls':    'ls [-l] [-a] [pattern]',
            'mkdir': 'mkdir <dirname>',
            'cd':    'cd <path>  (.., ~, relative)',
            'grep':  'grep [-i] [-v] <pattern> [file]',
            'echo':  'echo <text>',
            'copy':  'copy <file> to <dir>',
            'move':  'move <file> to <dir>',
        }
        print(help_text.get(command, f"No help for '{command}'"))
        return 0
    if command in ('ls', 'dir'):
        return ls_command(args_str) or 0
    elif command == 'echo':
        return echo_command(args_str) or 0
    elif command == 'grep':
        return grep_command(args_str) or 0
    elif command in ('rm', 'del'):
        return rm_command_ex(
            stripped_args,
            recursive=any(f in flags for f in ('-r','-rf','-fr','--recursive')),
            force=any(f in flags for f in ('-f','-rf','-fr','--force')),
            interactive='-i' in flags or '--interactive' in flags,
            dry_run='-n' in flags or '--dry-run' in flags) or 0
    elif command in command_functions:
        result = command_functions[command](stripped_args)
        return result if isinstance(result, int) else 0
    elif command in no_args_command_functions:
        result = no_args_command_functions[command]()
        return result if isinstance(result, int) else 0
    else:
        # Check user apps before giving up
        result = _run_user_app(command)
        if result is not None:
            return result
        print(f"'{command}' is not recognized as an internal or external command")
        return 127

# ─── Pipeline runner ──────────────────────────────────────────────────────────

def _run_pipeline(segment):
    stages = _split_on_op(segment, '|')
    stdin_data = None
    exit_code  = 0
    for i, stage in enumerate(stages):
        stage    = stage.strip()
        is_last  = (i == len(stages) - 1)
        clean_stage, redirects = _parse_redirects(stage)
        for op, target in redirects:
            if op == '<' and target:
                stdin_data = _read_vfile(target) or ''
        capture = not is_last or any(op in ('>','>>','&>','2>') for op, _ in redirects)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf if capture else sys.stdout):
            exit_code = _dispatch_single(clean_stage, stdin_data)
        output = buf.getvalue() if capture else ''
        for op, target in redirects:
            if op in ('>', '2>', '&>') and target:
                _write_vfile(target, output, append=False); output = ''
            elif op == '>>' and target:
                _write_vfile(target, output, append=True);  output = ''
        stdin_data = output if not is_last else None
        if is_last and output:
            print(output, end='')
    return exit_code

# ─── Main command processor ───────────────────────────────────────────────────

def process_commands():
    global _last_exit
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
            run = True if i == 0 else (_last_exit == 0 if ops[i-1] == '&&' else _last_exit != 0)
            if run:
                _last_exit = _run_pipeline(seg)
