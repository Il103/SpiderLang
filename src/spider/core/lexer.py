"""
SpiderLang Lexer — مبني يدوي 100% من الصفر
لا يستخدم regex ولا مكتبات خارجية للـ parsing
يمشي حرف حرف ويطلع Tokens
"""

from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # Single char
    LPAREN = auto(); RPAREN = auto()
    LBRACE = auto(); RBRACE = auto()
    LBRACK = auto(); RBRACK = auto()
    COMMA = auto(); DOT = auto(); COLON = auto(); SEMICOLON = auto()
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); PERCENT = auto()
    # One or two char
    EQ = auto(); EQEQ = auto(); NEQ = auto()
    LT = auto(); GT = auto(); LTE = auto(); GTE = auto()
    BANG = auto(); AND = auto(); OR = auto()
    ARROW = auto()  # =>
    # Literals
    IDENTIFIER = auto(); NUMBER = auto(); STRING = auto()
    # Keywords
    LET = auto(); FUNC = auto(); IF = auto(); ELSE = auto()
    RETURN = auto(); PRINT = auto(); USE = auto(); AS = auto()
    BOARD = auto(); TRUE = auto(); FALSE = auto(); NULL = auto()
    # Special
    EOF = auto()

KEYWORDS = {
    "let": TokenType.LET,
    "func": TokenType.FUNC,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "return": TokenType.RETURN,
    "print": TokenType.PRINT,
    "use": TokenType.USE,
    "as": TokenType.AS,
    "board": TokenType.BOARD,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
}

@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: object
    line: int
    col: int

    def __repr__(self):
        return f"{self.type.name}('{self.lexeme}' @ {self.line}:{self.col})"

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, source: str, filename: str = "<input>"):
        self.source = source
        self.filename = filename
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.col = 1
        self.start_col = 1

    def scan(self):
        while not self.is_at_end():
            self.start = self.current
            self.start_col = self.col
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.col))
        return self.tokens

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        c = self.source[self.current]
        self.current += 1
        if c == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def match(self, expected):
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.col += 1
        return True

    def add_token(self, type_, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type_, text, literal, self.line, self.start_col))

    def scan_token(self):
        c = self.advance()
        if c == '(':
            self.add_token(TokenType.LPAREN)
        elif c == ')':
            self.add_token(TokenType.RPAREN)
        elif c == '{':
            self.add_token(TokenType.LBRACE)
        elif c == '}':
            self.add_token(TokenType.RBRACE)
        elif c == '[':
            self.add_token(TokenType.LBRACK)
        elif c == ']':
            self.add_token(TokenType.RBRACK)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == ':':
            self.add_token(TokenType.COLON)
        elif c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == '.':
            self.add_token(TokenType.DOT)
        elif c == '+':
            self.add_token(TokenType.PLUS)
        elif c == '-':
            self.add_token(TokenType.MINUS)
        elif c == '*':
            self.add_token(TokenType.STAR)
        elif c == '%':
            self.add_token(TokenType.PERCENT)
        elif c == '/':
            if self.match('/'):
                # single line comment
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            elif self.match('*'):
                # block comment
                while not (self.peek() == '*' and self.peek_next() == '/') and not self.is_at_end():
                    self.advance()
                if not self.is_at_end():
                    self.advance() # *
                    self.advance() # /
            else:
                self.add_token(TokenType.SLASH)
        elif c == '!':
            self.add_token(TokenType.NEQ if self.match('=') else TokenType.BANG)
        elif c == '=':
            if self.match('='):
                self.add_token(TokenType.EQEQ)
            elif self.match('>'):
                self.add_token(TokenType.ARROW)
            else:
                self.add_token(TokenType.EQ)
        elif c == '<':
            self.add_token(TokenType.LTE if self.match('=') else TokenType.LT)
        elif c == '>':
            self.add_token(TokenType.GTE if self.match('=') else TokenType.GT)
        elif c == '&' and self.match('&'):
            self.add_token(TokenType.AND)
        elif c == '|' and self.match('|'):
            self.add_token(TokenType.OR)
        elif c in (' ', '\r', '\t', '\n'):
            pass  # ignore
        elif c == '"':
            self.string('"')
        elif c == "'":
            self.string("'")
        elif c.isdigit():
            self.number()
        elif c.isalpha() or c == '_':
            self.identifier()
        else:
            raise LexerError(f"[{self.filename}:{self.line}:{self.start_col}] Unexpected character '{c}'")

    def string(self, quote):
        # supports interpolation like "Hello {name}" -> we keep raw, interpreter will handle
        value = ""
        while self.peek() != quote and not self.is_at_end():
            if self.peek() == '\\':
                self.advance() # \
                esc = self.advance()
                if esc == 'n':
                    value += '\n'
                elif esc == 't':
                    value += '\t'
                elif esc == 'r':
                    value += '\r'
                elif esc == '\\':
                    value += '\\'
                elif esc == '"':
                    value += '"'
                elif esc == "'":
                    value += "'"
                else:
                    value += esc
            elif self.peek() == '\n':
                self.line += 1
                self.col = 1
                value += self.advance()
            else:
                value += self.advance()
        if self.is_at_end():
            raise LexerError(f"[{self.filename}:{self.line}:{self.start_col}] Unterminated string")
        self.advance() # closing quote
        self.add_token(TokenType.STRING, value)

    def number(self):
        while self.peek().isdigit():
            self.advance()
        # fractional part
        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance() # .
            while self.peek().isdigit():
                self.advance()
            text = self.source[self.start:self.current]
            self.add_token(TokenType.NUMBER, float(text))
        else:
            text = self.source[self.start:self.current]
            # keep as int if no dot, but lexer already consumed only digits
            self.add_token(TokenType.NUMBER, int(text))

    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        text = self.source[self.start:self.current]
        ttype = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self.add_token(ttype)

def tokenize(source: str, filename: str = "<input>"):
    return Lexer(source, filename).scan()
