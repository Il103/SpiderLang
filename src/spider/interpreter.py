"""
SpiderLang Interpreter — Tree-walk VM built from scratch
Handles sizes (B/KB/MB/GB/TB/PB/EB), board DSL, FFI, functions, etc.
All in English, handmade.
"""

import os
import re
import math
from .ast_nodes import *

# === Size system ===
# Binary units (1024) for Android partitions
SIZE_UNITS = {
    "B": 1,
    "KB": 1024,
    "KIB": 1024,
    "MB": 1024**2,
    "MIB": 1024**2,
    "GB": 1024**3,
    "GIB": 1024**3,
    "TB": 1024**4,
    "TIB": 1024**4,
    "PB": 1024**5,
    "PIB": 1024**5,
    "EB": 1024**6,
    "EIB": 1024**6,
    # also lowercase
    "b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4, "pb": 1024**5, "eb": 1024**6,
    "kib": 1024, "mib": 1024**2, "gib": 1024**3, "tib": 1024**4, "pib": 1024**5, "eib": 1024**6,
}

# Keep original for display
SIZE_ORDER = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]

class SpiderSize:
    """Represents a size value stored as bytes, but remembers display."""
    def __init__(self, bytes_val):
        self.bytes = int(bytes_val)

    def to(self, unit):
        unit = unit.upper()
        if unit not in SIZE_UNITS or unit.lower() not in [k.lower() for k in SIZE_UNITS]:
            # normalize
            u = unit.upper()
            if u not in [k.upper() for k in SIZE_UNITS]:
                raise RuntimeError(f"Unknown size unit '{unit}'")
        # find factor
        factor = None
        for k, v in SIZE_UNITS.items():
            if k.upper() == unit.upper():
                factor = v
                break
        return self.bytes / factor

    def __add__(self, other):
        if isinstance(other, SpiderSize):
            return SpiderSize(self.bytes + other.bytes)
        if isinstance(other, (int, float)):
            return SpiderSize(self.bytes + other)
        return NotImplemented
    def __sub__(self, other):
        if isinstance(other, SpiderSize):
            return SpiderSize(self.bytes - other.bytes)
        if isinstance(other, (int, float)):
            return SpiderSize(self.bytes - other)
        return NotImplemented
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return SpiderSize(self.bytes * other)
        return NotImplemented
    def __rmul__(self, other):
        return self.__mul__(other)
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return SpiderSize(self.bytes / other)
        if isinstance(other, SpiderSize):
            return self.bytes / other.bytes
        return NotImplemented
    def __eq__(self, other):
        if isinstance(other, SpiderSize):
            return self.bytes == other.bytes
        if isinstance(other, (int, float)):
            return self.bytes == other
        return False
    def __lt__(self, other):
        if isinstance(other, SpiderSize):
            return self.bytes < other.bytes
        if isinstance(other, (int, float)):
            return self.bytes < other
        return NotImplemented
    def __le__(self, other):
        if isinstance(other, SpiderSize):
            return self.bytes <= other.bytes
        return NotImplemented
    def __gt__(self, other):
        if isinstance(other, SpiderSize):
            return self.bytes > other.bytes
        return NotImplemented
    def __ge__(self, other):
        if isinstance(other, SpiderSize):
            return self.bytes >= other.bytes
        return NotImplemented

    def __repr__(self):
        # auto pretty: choose largest unit that divides evenly
        b = self.bytes
        for unit in reversed(SIZE_ORDER):
            factor = SIZE_UNITS[unit]
            if b % factor == 0 and b >= factor:
                return f"{b // factor}.{unit} ({b} B)"
        return f"{b}.B"

    def __str__(self):
        return self.__repr__()

class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def define(self, name, value):
        self.values[name] = value

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise RuntimeError(f"Undefined variable '{name}'")

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def exists(self, name):
        if name in self.values:
            return True
        if self.parent:
            return self.parent.exists(name)
        return False

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class SpiderFunction:
    def __init__(self, decl: FuncStmt, closure: Environment, interpreter):
        self.decl = decl
        self.closure = closure
        self.interpreter = interpreter

    def bind(self, instance):
        # for methods later
        env = Environment(self.closure)
        env.define("this", instance)
        return SpiderFunction(self.decl, env, self.interpreter)

    def call(self, args):
        env = Environment(self.closure)
        if len(args) != len(self.decl.params):
            raise RuntimeError(f"Function '{self.decl.name}' expected {len(self.decl.params)} args but got {len(args)}")
        for p, a in zip(self.decl.params, args):
            env.define(p, a)
        try:
            self.interpreter.execute_block(self.decl.body.statements, env)
        except ReturnException as ret:
            return ret.value
        return None

    def __repr__(self):
        return f"<func {self.decl.name}>"

class SpiderLambda:
    def __init__(self, params, body, closure, interpreter):
        self.params = params
        self.body = body
        self.closure = closure
        self.interpreter = interpreter

    def call(self, args):
        if len(args) != len(self.params):
            raise RuntimeError(f"Lambda expected {len(self.params)} args but got {len(args)}")
        env = Environment(self.closure)
        for p, a in zip(self.params, args):
            env.define(p, a)
        # body is single expression
        return self.interpreter.evaluate(self.body, env)

    def __repr__(self):
        return f"<lambda {self.params}>"

class SpiderFFIModule:
    """Represents a foreign module loaded via `use`"""
    def __init__(self, lang, path, alias):
        self.lang = lang
        self.path = path
        self.alias = alias
        self.functions = {}
        self.loaded = False
        self.error = None

    def load(self, base_dir):
        # Resolve path relative to base_dir
        full = os.path.join(base_dir, self.path) if not os.path.isabs(self.path) else self.path
        if not os.path.exists(full):
            self.error = f"FFI file not found: {full}"
            return
        # For now, we simulate loading. Real impl would delegate to ffi/<lang>.py
        # Try to import via ffi plugins if available
        try:
            from .ffi import registry
            handler = registry.get(self.lang.lower())
            if handler:
                handler.load(self, full)
                self.loaded = True
            else:
                # generic: just store path, allow verify_sizes mock
                self.loaded = True
                # Create a mock verify function for cpp validators
                if self.lang == "cpp":
                    def verify_sizes(board):
                        # board is dict-like
                        print(f"[{self.alias}] cpp verify_sizes called with {board}")
                        return True
                    self.functions["verify_sizes"] = verify_sizes
                    self.functions["verify"] = verify_sizes
                elif self.lang == "python":
                    # try to load python file
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(self.alias, full)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        for attr in dir(mod):
                            if not attr.startswith("_"):
                                self.functions[attr] = getattr(mod, attr)
        except Exception as e:
            self.error = str(e)

    def get(self, name):
        if name in self.functions:
            return self.functions[name]
        raise RuntimeError(f"FFI module '{self.alias}' has no member '{name}' (lang={self.lang})")

    def __repr__(self):
        return f"<ffi {self.lang} '{self.path}' as {self.alias}>"

class Interpreter:
    def __init__(self, base_dir=".", filename="<input>"):
        self.globals = Environment()
        self.env = self.globals
        self.base_dir = base_dir
        self.filename = filename
        self.ffi_modules = {}
        self.board_data = None
        self.output = []

        # builtins
        self.globals.define("print", self.builtin_print)
        self.globals.define("len", lambda x: len(x) if hasattr(x, "__len__") else 0)
        self.globals.define("str", lambda x: str(x))
        self.globals.define("int", lambda x: int(x))
        self.globals.define("float", lambda x: float(x))

        # size helpers
        self.globals.define("bytes", lambda x: x.bytes if isinstance(x, SpiderSize) else int(x))

    def builtin_print(self, *args):
        # handle string interpolation already done in visit
        out = " ".join(self.stringify(a) for a in args)
        print(out)
        self.output.append(out)
        return None

    def stringify(self, v):
        if isinstance(v, SpiderSize):
            return str(v)
        if isinstance(v, bool):
            return "true" if v else "false"
        if v is None:
            return "null"
        if isinstance(v, list):
            return "[" + ", ".join(self.stringify(e) for e in v) + "]"
        if isinstance(v, dict):
            inner = ", ".join(f"{k}: {self.stringify(val)}" for k, val in v.items())
            return "{" + inner + "}"
        if isinstance(v, SpiderFunction) or isinstance(v, SpiderLambda) or isinstance(v, SpiderFFIModule):
            return repr(v)
        return str(v)

    def interpolate_string(self, s, env):
        # Handle "Hello {name} and {board.arch}" style
        # Find {expr} patterns, evaluate expr
        def repl(m):
            expr_str = m.group(1).strip()
            if not expr_str:
                return ""
            try:
                from .lexer import tokenize
                from .parser import Parser
                toks = tokenize(expr_str, "<interp>")
                parser = Parser(toks, "<interp>")
                # Parse as expression, not full program (to avoid board declaration confusion)
                expr = parser.expression()
                val = self.evaluate(expr, env)
                return self.stringify(val)
            except Exception as e:
                return f"{{ERR:{e}}}"
        # Use regex to find { ... } but not escaped
        # This will also handle nested? Keep simple
        pattern = re.compile(r'\{([^{}]+)\}')
        # Only interpolate if contains {
        if "{" in s and "}" in s:
            try:
                return pattern.sub(repl, s)
            except:
                return s
        return s

    def interpret(self, program: Program):
        for stmt in program.statements:
            self.execute(stmt)

    def execute(self, stmt):
        method = f"visit_{type(stmt).__name__}"
        fn = getattr(self, method, None)
        if fn:
            return fn(stmt)
        else:
            # expression?
            return self.evaluate(stmt, self.env)

    def execute_block(self, statements, env):
        prev = self.env
        self.env = env
        try:
            for s in statements:
                self.execute(s)
        finally:
            self.env = prev

    # === statements ===
    def visit_LetStmt(self, stmt: LetStmt):
        val = self.evaluate(stmt.value, self.env)
        self.env.define(stmt.name, val)

    def visit_FuncStmt(self, stmt: FuncStmt):
        func = SpiderFunction(stmt, self.env, self)
        self.env.define(stmt.name, func)

    def visit_BoardStmt(self, stmt: BoardStmt):
        # Build board dict recursively
        board = {}
        for k, v in stmt.fields:
            val = self.evaluate(v, self.env)
            # if val is dict-like from nested parsing, keep
            board[k] = val
        # store both as variable "board" and as interpreter board_data
        self.env.define("board", board)
        self.board_data = board
        # also define in globals for interpolation
        self.globals.define("board", board)
        return board

    def visit_UseStmt(self, stmt: UseStmt):
        mod = SpiderFFIModule(stmt.lang, stmt.path, stmt.alias)
        mod.load(self.base_dir)
        self.env.define(stmt.alias, mod)
        self.globals.define(stmt.alias, mod)
        self.ffi_modules[stmt.alias] = mod
        if mod.error:
            print(f"[warn] FFI load failed for {stmt.lang} '{stmt.path}': {mod.error}")

    def visit_IfStmt(self, stmt: IfStmt):
        cond = self.evaluate(stmt.condition, self.env)
        if self.is_truthy(cond):
            self.execute_block(stmt.then_branch.statements, Environment(self.env))
        elif stmt.else_branch:
            self.execute_block(stmt.else_branch.statements, Environment(self.env))

    def visit_ReturnStmt(self, stmt: ReturnStmt):
        val = self.evaluate(stmt.value, self.env) if stmt.value else None
        raise ReturnException(val)

    def visit_PrintStmt(self, stmt: PrintStmt):
        val = self.evaluate(stmt.value, self.env)
        # handle string interpolation for strings
        if isinstance(val, str):
            val = self.interpolate_string(val, self.env)
        self.builtin_print(val)

    def visit_ExprStmt(self, stmt: ExprStmt):
        val = self.evaluate(stmt.expr, self.env)
        # handle size auto-print? no
        return val

    def visit_Block(self, stmt: Block):
        self.execute_block(stmt.statements, Environment(self.env))

    # === expressions ===
    def evaluate(self, expr, env=None):
        if env is None:
            env = self.env
        # literal already?
        method = f"eval_{type(expr).__name__}"
        fn = getattr(self, method, None)
        if fn:
            return fn(expr, env)
        raise RuntimeError(f"No eval for {type(expr).__name__}")

    def eval_Literal(self, expr: Literal, env):
        # handle interpolated strings
        if isinstance(expr.value, str) and "{" in expr.value:
            return self.interpolate_string(expr.value, env)
        return expr.value

    def eval_Variable(self, expr: Variable, env):
        # check env chain
        if env.exists(expr.name):
            return env.get(expr.name)
        if self.globals.exists(expr.name):
            return self.globals.get(expr.name)
        raise RuntimeError(f"Undefined variable '{expr.name}'")

    def eval_Assign(self, expr: Assign, env):
        val = self.evaluate(expr.value, env)
        # assign must exist or define? For simplicity, assign defines if not exists, else update
        if env.exists(expr.name):
            env.assign(expr.name, val)
        elif self.globals.exists(expr.name):
            self.globals.assign(expr.name, val)
        else:
            env.define(expr.name, val)
        return val

    def eval_Binary(self, expr: Binary, env):
        # Handle assignment via Binary with op "="
        if expr.op == "=" and isinstance(expr.left, Get):
            obj = self.evaluate(expr.left.obj, env)
            val = self.evaluate(expr.right, env)
            # obj can be dict or FFI or generic
            if isinstance(obj, dict):
                obj[expr.left.name] = val
                return val
            else:
                # set attr if object has __dict__
                setattr(obj, expr.left.name, val)
                return val
        left = self.evaluate(expr.left, env)
        right = self.evaluate(expr.right, env)
        op = expr.op
        # Size handling: if left or right is SpiderSize, handle
        # Also handle Get that is size unit like 64.MB
        # SpiderSize ops already defined, but string ops?
        try:
            if op == "+":
                if isinstance(left, SpiderSize) or isinstance(right, SpiderSize):
                    if isinstance(left, (int, float)) and isinstance(right, SpiderSize):
                        left = SpiderSize(left)
                    if isinstance(right, (int, float)) and isinstance(left, SpiderSize):
                        right = SpiderSize(right)
                    return left + right
                if isinstance(left, str) or isinstance(right, str):
                    return self.stringify(left) + self.stringify(right)
                return left + right
            elif op == "-":
                if isinstance(left, SpiderSize) and isinstance(right, SpiderSize):
                    return left - right
                if isinstance(left, SpiderSize) and isinstance(right, (int, float)):
                    return left - right
                return left - right
            elif op == "*":
                if isinstance(left, SpiderSize) and isinstance(right, (int, float)):
                    return left * right
                if isinstance(right, SpiderSize) and isinstance(left, (int, float)):
                    return right * left
                return left * right
            elif op == "/":
                if isinstance(left, SpiderSize) and isinstance(right, (int, float)):
                    return left / right
                if isinstance(left, SpiderSize) and isinstance(right, SpiderSize):
                    return left / right
                return left / right
            elif op == "%":
                return left % right
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == "<":
                return left < right
            elif op == ">":
                return left > right
            elif op == "<=":
                return left <= right
            elif op == ">=":
                return left >= right
            elif op == "&&" or op == "and":
                return self.is_truthy(left) and self.is_truthy(right)
            elif op == "||" or op == "or":
                return self.is_truthy(left) or self.is_truthy(right)
        except Exception as e:
            raise RuntimeError(f"Binary op '{op}' failed: {e} (left={left}, right={right})")
        raise RuntimeError(f"Unknown binary op '{op}'")

    def eval_Unary(self, expr: Unary, env):
        right = self.evaluate(expr.right, env)
        if expr.op == "-":
            if isinstance(right, SpiderSize):
                return SpiderSize(-right.bytes)
            return -right
        if expr.op == "!":
            return not self.is_truthy(right)
        raise RuntimeError(f"Unknown unary {expr.op}")

    def eval_Call(self, expr: Call, env):
        callee = self.evaluate(expr.callee, env)
        args = [self.evaluate(a, env) for a in expr.args]
        # Interpolate string args if needed? No
        if isinstance(callee, SpiderFunction):
            return callee.call(args)
        if isinstance(callee, SpiderLambda):
            return callee.call(args)
        if callable(callee):
            # builtin or FFI function
            return callee(*args)
        # If callee is FFI module get? Actually call like checker.verify_sizes(...)
        # That is Call(Get(Variable(checker), "verify_sizes"), args)
        # So callee should have been resolved via Get -> function
        raise RuntimeError(f"Cannot call {callee}")

    def eval_Get(self, expr: Get, env):
        obj = self.evaluate(expr.obj, env)
        name = expr.name
        # Special handling for SpiderSize units: 64.MB => obj is int, name is unit
        if isinstance(obj, (int, float)) and name.upper() in [k.upper() for k in SIZE_UNITS]:
            # find factor
            factor = None
            for k, v in SIZE_UNITS.items():
                if k.upper() == name.upper():
                    factor = v
                    break
            return SpiderSize(obj * factor)
        if isinstance(obj, SpiderSize) and name.lower().startswith("to"):
            # e.g., size.toKB() ? Not needed; we handle via method-like but sizes are not objects with methods in lang
            # support .bytes, .kb, .mb etc as property access returning conversion
            unit = name[2:] # after "to"
            if unit.upper() in [k.upper() for k in SIZE_UNITS]:
                return obj.to(unit)
        if isinstance(obj, SpiderSize):
            # allow .B, .KB, etc as getter that converts
            if name.upper() in [k.upper() for k in SIZE_UNITS]:
                # e.g., (64.MB).KB => bytes / KB
                return obj.to(name)
            if name == "bytes":
                return obj.bytes
            # also show string
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
            # allow method-like: .map for lists? no dict
            raise RuntimeError(f"Dict has no key '{name}'")
        if isinstance(obj, list):
            if name == "map":
                # return function that takes lambda
                def _map(fn):
                    result = []
                    for item in obj:
                        if isinstance(fn, SpiderLambda):
                            result.append(fn.call([item]))
                        elif callable(fn):
                            result.append(fn(item))
                        else:
                            raise RuntimeError("map expects function")
                    return result
                return _map
            if name == "filter":
                def _filter(fn):
                    res = []
                    for item in obj:
                        ok = fn.call([item]) if isinstance(fn, SpiderLambda) else fn(item)
                        if ok:
                            res.append(item)
                    return res
                return _filter
            if name == "len" or name == "length":
                return len(obj)
        if isinstance(obj, SpiderFFIModule):
            return obj.get(name)
        if isinstance(obj, str):
            if name == "len" or name == "length":
                return len(obj)
        # generic attribute
        try:
            return getattr(obj, name)
        except:
            raise RuntimeError(f"Cannot get '{name}' from {obj}")

    def eval_Index(self, expr: Index, env):
        obj = self.evaluate(expr.obj, env)
        idx = self.evaluate(expr.index, env)
        if isinstance(obj, (list, str, dict)):
            return obj[idx]
        raise RuntimeError(f"Cannot index {obj}")

    def eval_ListLiteral(self, expr: ListLiteral, env):
        return [self.evaluate(e, env) for e in expr.elements]

    def eval_DictLiteral(self, expr: DictLiteral, env):
        d = {}
        for k, v in expr.pairs:
            d[k] = self.evaluate(v, env)
        return d

    def eval_Lambda(self, expr: Lambda, env):
        return SpiderLambda(expr.params, expr.body, env, self)

    def eval_Grouping(self, expr: Grouping, env):
        return self.evaluate(expr.expr, env)

    def is_truthy(self, v):
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, SpiderSize):
            return v.bytes != 0
        if isinstance(v, (str, list, dict)):
            return len(v) > 0
        return True
