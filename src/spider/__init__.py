"""
SpiderLang — one language, every Android device
Created by Beru

A modern, general-purpose language with universal FFI.
Extension: .spt / .spider (primary)  +  .st (second recovery/image language)
"""
__version__ = "3.0.0"
__author__ = "Beru"

from .core.lexer import tokenize, Lexer
from .core.parser import parse
from .core.interpreter import Interpreter, SpiderSize

def run_source(source: str, filename="<input>", base_dir="."):
    from .core.lexer import tokenize
    from .core.parser import parse
    tokens = tokenize(source, filename)
    program = parse(tokens, filename)
    interp = Interpreter(base_dir=base_dir, filename=filename)
    interp.interpret(program)
    return interp
