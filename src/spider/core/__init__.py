"""
SpiderLang core — the hand-built language engine (lexer, parser, AST, VM).
Everything is from scratch: no eval, no exec, no ANTLR, no PLY.
"""
from .lexer import tokenize, Lexer
from .parser import parse
from .interpreter import Interpreter, SpiderSize, SIZE_UNITS

__all__ = ["tokenize", "Lexer", "parse", "Interpreter", "SpiderSize", "SIZE_UNITS"]
