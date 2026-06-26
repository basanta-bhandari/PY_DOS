"""
RubOS — PY_DOS Rubus CLI Language Engine
BASIC-inspired, geared for writing CLI tools inside PY_DOS.

Syntax quick-reference:
  let x = 5
  let name = "hello"
  let arr = [1, 2, 3]
  println "Hello " + name
  ask "Enter name: " -> name
  if x > 3 then ... elif x > 1 then ... else ... end
  while x > 0 do ... end
  loop 5 times ... end
  for i = 1 to 10 do ... end
  def greet(name) ... return "hi " + name ... end
  let r = greet("world")
  append arr "item"
  clear | pause | pause "msg" | color "cyan" | exit | exit 1
  read_file "notes.txt" -> content
  write_file "out.txt" content
  list_dir -> files
  menu ["Yes", "No"] -> choice
  # this is a comment
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
import sys
import os

# ─── Errors ───────────────────────────────────────────────────────────────────

class RubosError(Exception):
    def __init__(self, kind, message, line, source_lines=None):
        self.kind = kind
        self.message = message
        self.line = line
        self.source_lines = source_lines or []
        super().__init__(self.format())

    def format(self):
        width = 54
        bar = '─' * width
        lines = [
            f"┌─ RubOS {self.kind} {'─' * (width - len(self.kind) - 2)}┐",
            f"│  Line {self.line:<{width-7}}│",
        ]
        if self.source_lines and 0 < self.line <= len(self.source_lines):
            src = self.source_lines[self.line - 1].rstrip()
            lines.append(f"│                                                      │")
            snippet = f"  {self.line:>3} │  {src}"
            lines.append(f"│  {snippet:<{width-2}}│")
            lines.append(f"│                                                      │")
        lines.append(f"│  {self.message:<{width-2}}│")
        lines.append(f"└{'─' * width}┘")
        return '\n'.join(lines)

class ReturnSignal(Exception):
    def __init__(self, value): self.value = value

class ExitSignal(Exception):
    def __init__(self, code=0): self.code = code

# ─── Tokens ───────────────────────────────────────────────────────────────────

KEYWORDS = {
    'let','if','elif','else','then','end','while','do','loop','times',
    'for','to','def','return','and','or','not','true','false',
    'print','println','ask','clear','pause','color','exit',
    'read_file','write_file','list_dir','menu','append','len',
}

@dataclass
class Token:
    type: str   # KW IDENT NUM STR OP ARROW LPAREN RPAREN LBRACK RBRACK COMMA NEWLINE EOF
    value: Any
    line: int

def tokenize(source):
    tokens = []
    lines = source.split('\n')
    i = 0
    src_len = len(source)
    line_no = 1

    def peek(n=1): return source[i:i+n] if i+n <= src_len else ''
    def add(t, v, ln): tokens.append(Token(t, v, ln))

    while i < src_len:
        c = source[i]

        # Newline
        if c == '\n':
            if not tokens or tokens[-1].type != 'NEWLINE':
                add('NEWLINE', '\n', line_no)
            line_no += 1
            i += 1
            continue

        # Whitespace (not newline)
        if c in ' \t\r':
            i += 1
            continue

        # Comment
        if c == '#':
            while i < src_len and source[i] != '\n':
                i += 1
            continue

        # String
        if c in ('"', "'"):
            quote = c
            i += 1
            buf = []
            start_line = line_no
            while i < src_len and source[i] != quote:
                if source[i] == '\\':
                    i += 1
                    esc = source[i] if i < src_len else ''
                    buf.append({'n':'\n','t':'\t','\\':'\\','"':'"',"'":"'"}.get(esc, esc))
                else:
                    buf.append(source[i])
                if source[i] == '\n': line_no += 1
                i += 1
            if i >= src_len:
                raise RubosError("SyntaxError", "Unterminated string literal", start_line, lines)
            i += 1
            add('STR', ''.join(buf), start_line)
            continue

        # Number
        if c.isdigit() or (c == '-' and source[i+1:i+2].isdigit() and (not tokens or tokens[-1].type in ('NEWLINE','OP','LPAREN','LBRACK','COMMA','KW'))):
            buf = [c]; i += 1
            while i < src_len and (source[i].isdigit() or source[i] == '.'):
                buf.append(source[i]); i += 1
            val = float(''.join(buf)) if '.' in buf else int(''.join(buf))
            add('NUM', val, line_no)
            continue

        # Arrow ->
        if c == '-' and peek(2) == '->':
            add('ARROW', '->', line_no); i += 2; continue

        # Two-char operators
        two = peek(2)
        if two in ('==','!=','<=','>=','->','..'):
            add('OP', two, line_no); i += 2; continue

        # Single-char operators and punctuation
        if c in '+-*/%<>':
            add('OP', c, line_no); i += 1; continue
        if c == '=':
            add('OP', '=', line_no); i += 1; continue
        if c == '(':
            add('LPAREN', '(', line_no); i += 1; continue
        if c == ')':
            add('RPAREN', ')', line_no); i += 1; continue
        if c == '[':
            add('LBRACK', '[', line_no); i += 1; continue
        if c == ']':
            add('RBRACK', ']', line_no); i += 1; continue
        if c == ',':
            add('COMMA', ',', line_no); i += 1; continue

        # Identifier or keyword
        if c.isalpha() or c == '_':
            buf = []
            while i < src_len and (source[i].isalnum() or source[i] == '_'):
                buf.append(source[i]); i += 1
            word = ''.join(buf)
            if word in KEYWORDS:
                add('KW', word, line_no)
            else:
                add('IDENT', word, line_no)
            continue

        raise RubosError("SyntaxError", f"Unexpected character: '{c}'", line_no, lines)

    add('EOF', None, line_no)
    return tokens

# ─── AST Nodes ────────────────────────────────────────────────────────────────

@dataclass
class LetStmt:
    name: str; expr: Any; line: int

@dataclass
class AssignIndexStmt:
    name: str; index: Any; expr: Any; line: int

@dataclass
class PrintStmt:
    expr: Any; newline: bool; line: int

@dataclass
class AskStmt:
    prompt: Any; var: str; line: int

@dataclass
class IfStmt:
    cond: Any; body: List; elifs: List; else_body: List; line: int

@dataclass
class WhileStmt:
    cond: Any; body: List; line: int

@dataclass
class LoopTimesStmt:
    count: Any; body: List; line: int

@dataclass
class ForStmt:
    var: str; start: Any; end: Any; body: List; line: int

@dataclass
class DefStmt:
    name: str; params: List[str]; body: List; line: int

@dataclass
class ReturnStmt:
    expr: Any; line: int

@dataclass
class CallStmt:
    name: str; args: List; line: int

@dataclass
class AppendStmt:
    arr: str; val: Any; line: int

@dataclass
class ClearStmt:
    line: int

@dataclass
class PauseStmt:
    msg: Any; line: int

@dataclass
class ColorStmt:
    color: Any; line: int

@dataclass
class ExitStmt:
    code: Any; line: int

@dataclass
class ReadFileStmt:
    filename: Any; var: str; line: int

@dataclass
class WriteFileStmt:
    filename: Any; expr: Any; line: int

@dataclass
class ListDirStmt:
    var: str; line: int

@dataclass
class MenuStmt:
    options: Any; var: str; line: int

# Expressions
@dataclass
class BinOp:
    op: str; left: Any; right: Any; line: int

@dataclass
class UnaryOp:
    op: str; operand: Any; line: int

@dataclass
class Literal:
    value: Any; line: int

@dataclass
class VarRef:
    name: str; line: int

@dataclass
class CallExpr:
    name: str; args: List; line: int

@dataclass
class IndexExpr:
    obj: Any; index: Any; line: int

@dataclass
class ListLiteral:
    items: List; line: int

@dataclass
class LenExpr:
    expr: Any; line: int

# ─── Parser ───────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens, source_lines):
        self.tokens = tokens
        self.pos = 0
        self.src = source_lines

    def cur(self): return self.tokens[self.pos]
    def peek(self, n=1): return self.tokens[min(self.pos+n, len(self.tokens)-1)]

    def eat(self, type_=None, value=None):
        t = self.cur()
        if type_ and t.type != type_:
            raise RubosError("SyntaxError",
                f"Expected {type_} but got {t.type} '{t.value}'", t.line, self.src)
        if value and t.value != value:
            raise RubosError("SyntaxError",
                f"Expected '{value}' but got '{t.value}'", t.line, self.src)
        self.pos += 1
        return t

    def skip_newlines(self):
        while self.cur().type == 'NEWLINE':
            self.pos += 1

    def eat_newline(self):
        if self.cur().type == 'NEWLINE':
            self.pos += 1
        elif self.cur().type != 'EOF':
            raise RubosError("SyntaxError",
                f"Expected end of line but got '{self.cur().value}'",
                self.cur().line, self.src)

    def parse(self):
        self.skip_newlines()
        stmts = []
        while self.cur().type != 'EOF':
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return stmts

    def parse_block(self, *stop_kws):
        """Parse statements until a keyword in stop_kws."""
        stmts = []
        self.skip_newlines()
        while self.cur().type != 'EOF':
            if self.cur().type == 'KW' and self.cur().value in stop_kws:
                break
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return stmts

    def parse_stmt(self):
        t = self.cur()

        if t.type == 'NEWLINE':
            self.pos += 1
            return self.parse_stmt()

        if t.type == 'KW':
            if t.value == 'let':         return self.parse_let()
            if t.value in ('print','println'): return self.parse_print()
            if t.value == 'ask':         return self.parse_ask()
            if t.value == 'if':          return self.parse_if()
            if t.value == 'while':       return self.parse_while()
            if t.value == 'loop':        return self.parse_loop()
            if t.value == 'for':         return self.parse_for()
            if t.value == 'def':         return self.parse_def()
            if t.value == 'return':      return self.parse_return()
            if t.value == 'append':      return self.parse_append()
            if t.value == 'clear':       ln=t.line; self.pos+=1; self.eat_newline(); return ClearStmt(ln)
            if t.value == 'pause':       return self.parse_pause()
            if t.value == 'color':       return self.parse_color()
            if t.value == 'exit':        return self.parse_exit()
            if t.value == 'read_file':   return self.parse_read_file()
            if t.value == 'write_file':  return self.parse_write_file()
            if t.value == 'list_dir':    return self.parse_list_dir()
            if t.value == 'menu':        return self.parse_menu()

        # Function call as statement: name(args)
        if t.type == 'IDENT' and self.peek().type == 'LPAREN':
            return self.parse_call_stmt()

        raise RubosError("SyntaxError", f"Unexpected token '{t.value}'", t.line, self.src)

    def parse_let(self):
        ln = self.cur().line; self.eat('KW','let')
        name = self.eat('IDENT').value
        self.eat('OP','=')
        expr = self.parse_expr()
        self.eat_newline()
        return LetStmt(name, expr, ln)

    def parse_print(self):
        t = self.eat('KW'); ln = t.line
        newline = (t.value == 'println')
        expr = self.parse_expr()
        self.eat_newline()
        return PrintStmt(expr, newline, ln)

    def parse_ask(self):
        ln = self.cur().line; self.eat('KW','ask')
        prompt = self.parse_expr()
        self.eat('ARROW')
        var = self.eat('IDENT').value
        self.eat_newline()
        return AskStmt(prompt, var, ln)

    def parse_if(self):
        ln = self.cur().line; self.eat('KW','if')
        cond = self.parse_expr()
        self.eat('KW','then'); self.eat_newline()
        body = self.parse_block('elif','else','end')
        elifs = []
        while self.cur().type == 'KW' and self.cur().value == 'elif':
            self.pos += 1
            ec = self.parse_expr(); self.eat('KW','then'); self.eat_newline()
            eb = self.parse_block('elif','else','end')
            elifs.append((ec, eb))
        else_body = []
        if self.cur().type == 'KW' and self.cur().value == 'else':
            self.pos += 1; self.eat_newline()
            else_body = self.parse_block('end')
        self.eat('KW','end'); self.eat_newline()
        return IfStmt(cond, body, elifs, else_body, ln)

    def parse_while(self):
        ln = self.cur().line; self.eat('KW','while')
        cond = self.parse_expr(); self.eat('KW','do'); self.eat_newline()
        body = self.parse_block('end')
        self.eat('KW','end'); self.eat_newline()
        return WhileStmt(cond, body, ln)

    def parse_loop(self):
        ln = self.cur().line; self.eat('KW','loop')
        count = self.parse_expr(); self.eat('KW','times'); self.eat_newline()
        body = self.parse_block('end')
        self.eat('KW','end'); self.eat_newline()
        return LoopTimesStmt(count, body, ln)

    def parse_for(self):
        ln = self.cur().line; self.eat('KW','for')
        var = self.eat('IDENT').value; self.eat('OP','=')
        start = self.parse_expr(); self.eat('KW','to')
        end = self.parse_expr()
        if self.cur().type == 'KW' and self.cur().value == 'do':
            self.pos += 1  # optional 'do'
        self.eat_newline()
        body = self.parse_block('end')
        self.eat('KW','end'); self.eat_newline()
        return ForStmt(var, start, end, body, ln)

    def parse_def(self):
        ln = self.cur().line; self.eat('KW','def')
        name = self.eat('IDENT').value; self.eat('LPAREN')
        params = []
        while self.cur().type != 'RPAREN':
            params.append(self.eat('IDENT').value)
            if self.cur().type == 'COMMA': self.pos += 1
        self.eat('RPAREN'); self.eat_newline()
        body = self.parse_block('end')
        self.eat('KW','end'); self.eat_newline()
        return DefStmt(name, params, body, ln)

    def parse_return(self):
        ln = self.cur().line; self.eat('KW','return')
        expr = None
        if self.cur().type not in ('NEWLINE','EOF'):
            expr = self.parse_expr()
        self.eat_newline()
        return ReturnStmt(expr, ln)

    def parse_call_stmt(self):
        ln = self.cur().line
        name = self.eat('IDENT').value; self.eat('LPAREN')
        args = self.parse_args(); self.eat('RPAREN'); self.eat_newline()
        return CallStmt(name, args, ln)

    def parse_append(self):
        ln = self.cur().line; self.eat('KW','append')
        arr = self.eat('IDENT').value
        val = self.parse_expr(); self.eat_newline()
        return AppendStmt(arr, val, ln)

    def parse_pause(self):
        ln = self.cur().line; self.eat('KW','pause')
        msg = None
        if self.cur().type not in ('NEWLINE','EOF'):
            msg = self.parse_expr()
        self.eat_newline()
        return PauseStmt(msg, ln)

    def parse_color(self):
        ln = self.cur().line; self.eat('KW','color')
        c = self.parse_expr(); self.eat_newline()
        return ColorStmt(c, ln)

    def parse_exit(self):
        ln = self.cur().line; self.eat('KW','exit')
        code = None
        if self.cur().type not in ('NEWLINE','EOF'):
            code = self.parse_expr()
        self.eat_newline()
        return ExitStmt(code, ln)

    def parse_read_file(self):
        ln = self.cur().line; self.eat('KW','read_file')
        fn = self.parse_expr(); self.eat('ARROW')
        var = self.eat('IDENT').value; self.eat_newline()
        return ReadFileStmt(fn, var, ln)

    def parse_write_file(self):
        ln = self.cur().line; self.eat('KW','write_file')
        fn = self.parse_expr()
        expr = self.parse_expr(); self.eat_newline()
        return WriteFileStmt(fn, expr, ln)

    def parse_list_dir(self):
        ln = self.cur().line; self.eat('KW','list_dir')
        self.eat('ARROW'); var = self.eat('IDENT').value; self.eat_newline()
        return ListDirStmt(var, ln)

    def parse_menu(self):
        ln = self.cur().line; self.eat('KW','menu')
        opts = self.parse_expr(); self.eat('ARROW')
        var = self.eat('IDENT').value; self.eat_newline()
        return MenuStmt(opts, var, ln)

    def parse_args(self):
        args = []
        while self.cur().type not in ('RPAREN','RBRACK','EOF'):
            args.append(self.parse_expr())
            if self.cur().type == 'COMMA': self.pos += 1
        return args

    # Expression parsing (recursive descent)
    def parse_expr(self):   return self.parse_or()
    def parse_or(self):
        left = self.parse_and()
        while self.cur().type == 'KW' and self.cur().value == 'or':
            ln = self.cur().line; self.pos += 1
            left = BinOp('or', left, self.parse_and(), ln)
        return left
    def parse_and(self):
        left = self.parse_not()
        while self.cur().type == 'KW' and self.cur().value == 'and':
            ln = self.cur().line; self.pos += 1
            left = BinOp('and', left, self.parse_not(), ln)
        return left
    def parse_not(self):
        if self.cur().type == 'KW' and self.cur().value == 'not':
            ln = self.cur().line; self.pos += 1
            return UnaryOp('not', self.parse_not(), ln)
        return self.parse_compare()
    def parse_compare(self):
        left = self.parse_add()
        if self.cur().type == 'OP' and self.cur().value in ('==','!=','<','>','<=','>='):
            ln = self.cur().line; op = self.cur().value; self.pos += 1
            return BinOp(op, left, self.parse_add(), ln)
        return left
    def parse_add(self):
        left = self.parse_mul()
        while self.cur().type == 'OP' and self.cur().value in ('+','-'):
            ln = self.cur().line; op = self.cur().value; self.pos += 1
            left = BinOp(op, left, self.parse_mul(), ln)
        return left
    def parse_mul(self):
        left = self.parse_unary()
        while self.cur().type == 'OP' and self.cur().value in ('*','/','%'):
            ln = self.cur().line; op = self.cur().value; self.pos += 1
            left = BinOp(op, left, self.parse_unary(), ln)
        return left
    def parse_unary(self):
        if self.cur().type == 'OP' and self.cur().value == '-':
            ln = self.cur().line; self.pos += 1
            return UnaryOp('-', self.parse_unary(), ln)
        return self.parse_primary()
    def parse_primary(self):
        t = self.cur(); ln = t.line
        if t.type == 'NUM':  self.pos += 1; return Literal(t.value, ln)
        if t.type == 'STR':  self.pos += 1; return Literal(t.value, ln)
        if t.type == 'KW' and t.value == 'true':  self.pos += 1; return Literal(True, ln)
        if t.type == 'KW' and t.value == 'false': self.pos += 1; return Literal(False, ln)
        if t.type == 'LBRACK':
            self.pos += 1
            items = self.parse_args()
            self.eat('RBRACK')
            return ListLiteral(items, ln)
        if t.type == 'KW' and t.value == 'len':
            self.pos += 1; self.eat('LPAREN')
            expr = self.parse_expr(); self.eat('RPAREN')
            return LenExpr(expr, ln)
        if t.type == 'IDENT':
            name = t.value; self.pos += 1
            if self.cur().type == 'LPAREN':
                self.eat('LPAREN'); args = self.parse_args(); self.eat('RPAREN')
                node = CallExpr(name, args, ln)
            else:
                node = VarRef(name, ln)
            if self.cur().type == 'LBRACK':
                self.pos += 1; idx = self.parse_expr(); self.eat('RBRACK')
                return IndexExpr(node, idx, ln)
            return node
        if t.type == 'LPAREN':
            self.pos += 1; expr = self.parse_expr(); self.eat('RPAREN')
            return expr
        raise RubosError("SyntaxError", f"Unexpected '{t.value}' in expression", ln, [])

# ─── Interpreter ──────────────────────────────────────────────────────────────

COLORS = {
    'red':'\033[31m','green':'\033[32m','yellow':'\033[33m','blue':'\033[34m',
    'magenta':'\033[35m','cyan':'\033[36m','white':'\033[37m','reset':'\033[0m',
    'bold':'\033[1m',
}

class Interpreter:
    def __init__(self, source_lines, ctx):
        self.src = source_lines
        self.ctx = ctx
        self.globals = {}
        self.call_stack = []  # list of local env dicts

    def env(self): return self.call_stack[-1] if self.call_stack else self.globals

    def get(self, name, line):
        for frame in reversed(self.call_stack):
            if name in frame: return frame[name]
        if name in self.globals: return self.globals[name]
        raise RubosError("NameError", f"Variable '{name}' is not defined", line, self.src)

    def set(self, name, value):
        if self.call_stack:
            self.call_stack[-1][name] = value
        else:
            self.globals[name] = value

    def run(self, stmts):
        for stmt in stmts:
            self.exec(stmt)

    def exec(self, node):
        t = type(node)

        if t is LetStmt:
            self.set(node.name, self.eval(node.expr))

        elif t is PrintStmt:
            val = self.eval(node.expr)
            end = '\n' if node.newline else ''
            print(self._to_str(val), end=end)

        elif t is AskStmt:
            prompt = self._to_str(self.eval(node.prompt))
            val = input(prompt)
            self.set(node.var, val)

        elif t is IfStmt:
            if self._truthy(self.eval(node.cond)):
                self.run(node.body)
            else:
                done = False
                for ec, eb in node.elifs:
                    if self._truthy(self.eval(ec)):
                        self.run(eb); done = True; break
                if not done:
                    self.run(node.else_body)

        elif t is WhileStmt:
            limit = 100_000; count = 0
            while self._truthy(self.eval(node.cond)):
                self.run(node.body)
                count += 1
                if count >= limit:
                    raise RubosError("RuntimeError", "Loop exceeded 100,000 iterations (infinite loop?)", node.line, self.src)

        elif t is LoopTimesStmt:
            n = self.eval(node.count)
            if not isinstance(n, (int, float)):
                raise RubosError("TypeError", f"'loop N times' expects a number, got {type(n).__name__}", node.line, self.src)
            for _ in range(int(n)):
                self.run(node.body)

        elif t is ForStmt:
            start = self.eval(node.start); end = self.eval(node.end)
            for i in range(int(start), int(end)+1):
                self.set(node.var, i)
                self.run(node.body)

        elif t is DefStmt:
            self.globals[node.name] = node

        elif t is ReturnStmt:
            val = self.eval(node.expr) if node.expr else None
            raise ReturnSignal(val)

        elif t is CallStmt:
            self._call(node.name, node.args, node.line)

        elif t is AppendStmt:
            arr = self.get(node.arr, node.line)
            if not isinstance(arr, list):
                raise RubosError("TypeError", f"'append' expects a list, got {type(arr).__name__}", node.line, self.src)
            arr.append(self.eval(node.val))

        elif t is ClearStmt:
            self.ctx.clear()

        elif t is PauseStmt:
            msg = self._to_str(self.eval(node.msg)) if node.msg else "Press Enter to continue..."
            input(msg)

        elif t is ColorStmt:
            c = self._to_str(self.eval(node.color)).lower()
            print(COLORS.get(c, ''), end='')

        elif t is ExitStmt:
            code = int(self.eval(node.code)) if node.code else 0
            raise ExitSignal(code)

        elif t is ReadFileStmt:
            fn = self._to_str(self.eval(node.filename))
            content = self.ctx.read_file(fn)
            if content is None:
                raise RubosError("IOError", f"File not found: '{fn}'", node.line, self.src)
            self.set(node.var, content)

        elif t is WriteFileStmt:
            fn = self._to_str(self.eval(node.filename))
            content = self._to_str(self.eval(node.expr))
            self.ctx.write_file(fn, content)

        elif t is ListDirStmt:
            self.set(node.var, self.ctx.list_dir())

        elif t is MenuStmt:
            opts = self.eval(node.options)
            if not isinstance(opts, list) or not opts:
                raise RubosError("TypeError", "'menu' expects a non-empty list", node.line, self.src)
            for i, o in enumerate(opts, 1):
                print(f"  {i}) {self._to_str(o)}")
            while True:
                try:
                    raw = input("Choice: ").strip()
                    idx = int(raw) - 1
                    if 0 <= idx < len(opts):
                        self.set(node.var, opts[idx])
                        break
                    print(f"  Enter a number between 1 and {len(opts)}")
                except ValueError:
                    print(f"  Enter a number between 1 and {len(opts)}")

    def eval(self, node):
        t = type(node)
        if t is Literal:  return node.value
        if t is VarRef:   return self.get(node.name, node.line)
        if t is ListLiteral: return [self.eval(i) for i in node.items]
        if t is LenExpr:
            v = self.eval(node.expr)
            if not isinstance(v, (list, str)):
                raise RubosError("TypeError", f"'len' expects string or list, got {type(v).__name__}", node.line, self.src)
            return len(v)
        if t is IndexExpr:
            obj = self.eval(node.obj); idx = self.eval(node.index)
            if not isinstance(obj, (list, str)):
                raise RubosError("TypeError", f"Can only index into list or string", node.line, self.src)
            if not isinstance(idx, (int, float)):
                raise RubosError("TypeError", f"Index must be a number", node.line, self.src)
            i = int(idx)
            if i < 0 or i >= len(obj):
                raise RubosError("IndexError", f"Index {i} out of range (length {len(obj)})", node.line, self.src)
            return obj[i]
        if t is CallExpr:
            return self._call(node.name, node.args, node.line)
        if t is UnaryOp:
            v = self.eval(node.operand)
            if node.op == '-':
                if not isinstance(v, (int, float)):
                    raise RubosError("TypeError", f"Cannot negate {type(v).__name__}", node.line, self.src)
                return -v
            if node.op == 'not': return not self._truthy(v)
        if t is BinOp:
            return self._binop(node)
        raise RubosError("InternalError", f"Unknown AST node: {t.__name__}", 0, self.src)

    def _binop(self, node):
        op = node.op
        # Short-circuit logic
        if op == 'and':
            return self._truthy(self.eval(node.left)) and self._truthy(self.eval(node.right))
        if op == 'or':
            return self._truthy(self.eval(node.left)) or self._truthy(self.eval(node.right))

        left = self.eval(node.left); right = self.eval(node.right)
        ln = node.line

        if op == '+':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            return self._to_str(left) + self._to_str(right)  # string concat

        if op == '-':
            self._assert_num(left, right, '-', ln)
            return left - right
        if op == '*':
            self._assert_num(left, right, '*', ln)
            return left * right
        if op == '/':
            self._assert_num(left, right, '/', ln)
            if right == 0:
                raise RubosError("ZeroDivisionError", "Cannot divide by zero", ln, self.src)
            return left / right
        if op == '%':
            self._assert_num(left, right, '%', ln)
            if right == 0:
                raise RubosError("ZeroDivisionError", "Cannot modulo by zero", ln, self.src)
            return left % right
        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '<':  return left < right
        if op == '>':  return left > right
        if op == '<=': return left <= right
        if op == '>=': return left >= right
        raise RubosError("SyntaxError", f"Unknown operator '{op}'", ln, self.src)

    def _call(self, name, arg_nodes, line):
        func = self.globals.get(name)
        if func is None:
            raise RubosError("NameError", f"Function '{name}' is not defined", line, self.src)
        if not isinstance(func, DefStmt):
            raise RubosError("TypeError", f"'{name}' is not a function", line, self.src)
        args = [self.eval(a) for a in arg_nodes]
        if len(args) != len(func.params):
            raise RubosError("TypeError",
                f"'{name}' expects {len(func.params)} argument(s), got {len(args)}", line, self.src)
        frame = dict(zip(func.params, args))
        self.call_stack.append(frame)
        try:
            self.run(func.body)
            return None
        except ReturnSignal as r:
            return r.value
        finally:
            self.call_stack.pop()

    def _assert_num(self, a, b, op, line):
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise RubosError("TypeError",
                f"Operator '{op}' requires numbers, got {type(a).__name__} and {type(b).__name__}",
                line, self.src)

    def _truthy(self, v):
        if v is None: return False
        if isinstance(v, bool): return v
        if isinstance(v, (int, float)): return v != 0
        if isinstance(v, str): return v != ''
        if isinstance(v, list): return len(v) > 0
        return True

    def _to_str(self, v):
        if isinstance(v, bool): return 'true' if v else 'false'
        if isinstance(v, float):
            return str(int(v)) if v == int(v) else str(v)
        if isinstance(v, list):
            return '[' + ', '.join(self._to_str(i) for i in v) + ']'
        return str(v) if v is not None else ''

# ─── Public API ───────────────────────────────────────────────────────────────

class PYDOSContext:
    """Passed to the interpreter so it can interact with PY_DOS's virtual FS."""
    def __init__(self, directory_contents, kernel, current_directory,
                 join_path, save_file_contents, save_filesystem):
        self._dc  = directory_contents
        self._k   = kernel
        self._cwd = current_directory
        self._jp  = join_path
        self._sfc = save_file_contents
        self._sf  = save_filesystem

    def read_file(self, name):
        p = self._jp(self._cwd, name)
        if p in self._dc:
            return self._dc[p].get('content', '')
        return None

    def write_file(self, name, content):
        p = self._jp(self._cwd, name)
        self._dc[p] = {'type': 'txt', 'content': content, 'created_in': self._cwd}
        self._k[self._cwd]['contents'][name] = {'type': 'file'}
        self._sfc(); self._sf()

    def list_dir(self):
        node = self._k.get(self._cwd, {})
        return list(node.get('contents', {}).keys())

    def clear(self):
        os.system('clear')


def run(source, ctx=None):
    """
    Compile and run a RubOS program.
    Returns exit code (0=success, nonzero=error/exit).
    ctx: PYDOSContext or None (for standalone testing).
    """
    if ctx is None:
        # Minimal stub for running outside PY_DOS
        class _StubCtx:
            def read_file(self, n): return None
            def write_file(self, n, c): pass
            def list_dir(self): return []
            def clear(self): print('\033[2J\033[H', end='')
        ctx = _StubCtx()

    source_lines = source.split('\n')
    try:
        tokens = tokenize(source)
        parser = Parser(tokens, source_lines)
        ast = parser.parse()
        interp = Interpreter(source_lines, ctx)
        interp.run(ast)
        return 0
    except RubosError as e:
        print(str(e))
        return 1
    except ExitSignal as e:
        return e.code
    except KeyboardInterrupt:
        print('\n[RubOS] Interrupted.')
        return 130
    except RecursionError:
        print(RubosError("RuntimeError", "Stack overflow — infinite recursion?", 0, source_lines))
        return 1


def check(source):
    """Parse only (no execution). Returns list of error strings, empty = OK."""
    source_lines = source.split('\n')
    errors = []
    try:
        tokens = tokenize(source)
        parser = Parser(tokens, source_lines)
        parser.parse()
    except RubosError as e:
        errors.append(str(e))
    return errors


# Run as standalone script for testing
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: rubus_engine.py <file.rub>")
        sys.exit(1)
    src = open(sys.argv[1]).read()
    sys.exit(run(src))