"""
SpiderLang — one language, every Android device
Created by Beru

A modern, general-purpose language with universal FFI.
Extension: .spt / .spider
"""
__version__ = "0.1.0"
__author__ = "Beru"

from .lexer import tokenize, Lexer
from .parser import parse
from .interpreter import Interpreter, SpiderSize

def run_source(source: str, filename="<input>", base_dir="."):
    from .lexer import tokenize
    from .parser import parse
    tokens = tokenize(source, filename)
    program = parse(tokens, filename)
    interp = Interpreter(base_dir=base_dir, filename=filename)
    interp.interpret(program)
    return interp
