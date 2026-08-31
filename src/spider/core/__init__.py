"""
SpiderLang core — the language engine (lexer, parser, AST, VM).
"""
from .lexer import tokenize, Lexer
from .parser import parse
from .interpreter import Interpreter, SpiderSize, SIZE_UNITS

__all__ = ["tokenize", "Lexer", "parse", "Interpreter", "SpiderSize", "SIZE_UNITS"]
