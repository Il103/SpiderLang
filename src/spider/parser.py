"""
SpiderLang Parser — Handwritten Recursive Descent from Scratch
No external parsing libraries, built entirely by hand.
"""
from .lexer import Token, TokenType
from .ast_nodes import *

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens, filename="<input>"):
        self.tokens = tokens
        self.filename = filename
        self.current = 0

    def parse(self):
        statements = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return Program(statements)

    # === helpers ===
    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, ttype):
        if self.is_at_end():
            return False
        return self.peek().type == ttype

    def match(self, *types):
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, ttype, msg):
        if self.check(ttype):
            return self.advance()
        tok = self.peek()
        raise ParseError(f"[{self.filename}:{tok.line}:{tok.col}] {msg} got {tok.lexeme}")

    # === declarations ===
    def declaration(self):
        if self.match(TokenType.LET):
            return self.let_declaration()
        if self.match(TokenType.FUNC):
            return self.func_declaration()
        if self.check(TokenType.BOARD):
            # Only treat as board declaration if followed by '{' (top-level board { ... })
            if self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == TokenType.LBRACE:
                return self.board_declaration()
            # otherwise treat as normal statement/expression (e.g., board.arch)
        if self.check(TokenType.USE):
            return self.use_declaration()
        return self.statement()

    def let_declaration(self):
        tok = self.consume(TokenType.IDENTIFIER, "Expected variable name after 'let'")
        self.consume(TokenType.EQ, "Expected '=' after variable name")
        value = self.expression()
        if self.match(TokenType.SEMICOLON):
            pass
        return LetStmt(tok.lexeme, value, tok.line, tok.col)

    def func_declaration(self):
        tok = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        params = []
        if not self.check(TokenType.RPAREN):
            while True:
                p = self.consume(TokenType.IDENTIFIER, "Expected param name")
                params.append(p.lexeme)
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RPAREN, "Expected ')' after params")
        self.consume(TokenType.LBRACE, "Expected '{' before function body")
        body = self.block()
        return FuncStmt(tok.lexeme, params, body, tok.line, tok.col)

    def board_declaration(self):
        tok = self.consume(TokenType.BOARD, "Expected 'board'")
        self.consume(TokenType.LBRACE, "Expected '{' after 'board'")
        fields = self.dict_entries()
        self.consume(TokenType.RBRACE, "Expected '}' after board block")
        return BoardStmt({}, fields, tok.line, tok.col)

    def dict_entries(self):
        pairs = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            # key can be identifier or string
            if self.check(TokenType.IDENTIFIER):
                key_tok = self.advance()
                key = key_tok.lexeme
            elif self.check(TokenType.STRING):
                key_tok = self.advance()
                key = key_tok.literal
            else:
                raise ParseError(f"[{self.filename}:{self.peek().line}:{self.peek().col}] Expected key in object")
            self.consume(TokenType.COLON, "Expected ':' after key")
            val = self.expression()
            # nested object literal already handled as expression, but also allow { } directly
            pairs.append((key, val))
            if not self.match(TokenType.COMMA):
                # allow optional comma and newlines
                if self.check(TokenType.RBRACE):
                    break
                # if no comma, continue if next is identifier/string (implicit)
                if self.check(TokenType.IDENTIFIER) or self.check(TokenType.STRING):
                    continue
                break
        return pairs

    def use_declaration(self):
        tok = self.consume(TokenType.USE, "Expected 'use'")
        # lang is identifier
        lang_tok = self.consume(TokenType.IDENTIFIER, "Expected language name after 'use'")
        path_tok = self.consume(TokenType.STRING, "Expected path string after language")
        self.consume(TokenType.AS, "Expected 'as' after path")
        alias_tok = self.consume(TokenType.IDENTIFIER, "Expected alias after 'as'")
        if self.match(TokenType.SEMICOLON):
            pass
        return UseStmt(lang_tok.lexeme, path_tok.literal, alias_tok.lexeme, tok.line, tok.col)

    def statement(self):
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.PRINT):
            # print(...) or print expr
            if self.match(TokenType.LPAREN):
                val = self.expression()
                self.consume(TokenType.RPAREN, "Expected ')' after print")
                if self.match(TokenType.SEMICOLON):
                    pass
                return PrintStmt(val, self.previous().line, self.previous().col)
            else:
                val = self.expression()
                if self.match(TokenType.SEMICOLON):
                    pass
                return PrintStmt(val, self.previous().line, self.previous().col)
        if self.check(TokenType.LBRACE):
            # block as statement
            self.consume(TokenType.LBRACE, "Expected '{'")
            b = self.block()
            return b
        return self.expr_statement()

    def block(self):
        stmts = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            stmts.append(self.declaration())
        self.consume(TokenType.RBRACE, "Expected '}' after block")
        return Block(stmts)

    def if_statement(self):
        tok = self.previous()
        # if condition { } else { }
        # condition may be parenthesized or not
        if self.match(TokenType.LPAREN):
            cond = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after condition")
        else:
            cond = self.expression()
        self.consume(TokenType.LBRACE, "Expected '{' after if condition")
        then_b = self.block()
        else_b = None
        if self.match(TokenType.ELSE):
            self.consume(TokenType.LBRACE, "Expected '{' after else")
            else_b = self.block()
        return IfStmt(cond, then_b, else_b, tok.line, tok.col)

    def return_statement(self):
        tok = self.previous()
        val = None
        if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE) and not self.is_at_end():
            # try to parse expression if present
            # peek if next is not } ; EOF
            try:
                # check if next token can start expr
                if self.check(TokenType.SEMICOLON):
                    pass
                else:
                    val = self.expression()
            except:
                val = None
        self.match(TokenType.SEMICOLON)
        return ReturnStmt(val, tok.line, tok.col)

    def expr_statement(self):
        expr = self.expression()
        self.match(TokenType.SEMICOLON)
        # line info from first token of expr if available
        return ExprStmt(expr, 1, 1)

    # === expressions ===
    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.logical_or()
        if self.match(TokenType.EQ):
            equals = self.previous()
            value = self.assignment()
            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            elif isinstance(expr, Get):
                # setter: obj.name = value => treat as special assign
                # we represent as Binary with op = "=" and left = Get
                return Binary(expr, "=", value)
            raise ParseError(f"[{self.filename}:{equals.line}:{equals.col}] Invalid assignment target")
        return expr

    def logical_or(self):
        expr = self.logical_and()
        while self.match(TokenType.OR):
            op = self.previous().lexeme
            right = self.logical_and()
            expr = Binary(expr, op, right)
        return expr

    def logical_and(self):
        expr = self.equality()
        while self.match(TokenType.AND):
            op = self.previous().lexeme
            right = self.equality()
            expr = Binary(expr, op, right)
        return expr

    def equality(self):
        expr = self.comparison()
        while self.match(TokenType.EQEQ, TokenType.NEQ):
            op = self.previous().lexeme
            right = self.comparison()
            expr = Binary(expr, op, right)
        return expr

    def comparison(self):
        expr = self.term()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.previous().lexeme
            right = self.term()
            expr = Binary(expr, op, right)
        return expr

    def term(self):
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.previous().lexeme
            right = self.factor()
            expr = Binary(expr, op, right)
        return expr

    def factor(self):
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.previous().lexeme
            right = self.unary()
            expr = Binary(expr, op, right)
        return expr

    def unary(self):
        if self.match(TokenType.MINUS, TokenType.BANG):
            op = self.previous().lexeme
            right = self.unary()
            return Unary(op, right)
        return self.call()

    def call(self):
        expr = self.primary()
        while True:
            if self.match(TokenType.LPAREN):
                args = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        args.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = Call(expr, args)
            elif self.match(TokenType.DOT):
                # property can be any identifier-like token (including board, arch etc)
                if self.match(TokenType.IDENTIFIER, TokenType.BOARD):
                    name_tok = self.previous()
                else:
                    name_tok = self.consume(TokenType.IDENTIFIER, "Expected property name after '.'")
                expr = Get(expr, name_tok.lexeme)
            elif self.match(TokenType.LBRACK):
                idx = self.expression()
                self.consume(TokenType.RBRACK, "Expected ']' after index")
                expr = Index(expr, idx)
            elif self.match(TokenType.ARROW):
                # lambda shorthand: x => x * 2  or (x,y) => ...
                # only if expr is Variable or previous was param list
                # handle: already parsed left as Variable, now => body
                body = self.expression()
                if isinstance(expr, Variable):
                    expr = Lambda([expr.name], body)
                elif isinstance(expr, ListLiteral):
                    # not used
                    pass
                else:
                    # treat as lambda with single param
                    pass
            else:
                break
        return expr

    def primary(self):
        if self.match(TokenType.FALSE):
            return Literal(False)
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.NULL):
            return Literal(None)
        if self.match(TokenType.NUMBER):
            return Literal(self.previous().literal)
        if self.match(TokenType.STRING):
            return Literal(self.previous().literal)
        if self.match(TokenType.IDENTIFIER, TokenType.BOARD):
            return Variable(self.previous().lexeme)
        if self.match(TokenType.LPAREN):
            # check for lambda params: (x, y) => expr
            # lookahead
            # if we have identifiers separated by commas then ) => then lambda
            # simple: parse as grouping, then check for =>
            # save position
            # For now handle grouping
            if self.check(TokenType.IDENTIFIER) or self.check(TokenType.RPAREN):
                # try to parse param list for lambda
                saved = self.current
                params = []
                is_lambda_params = False
                if self.check(TokenType.RPAREN):
                    # empty params ()
                    self.advance()
                    if self.check(TokenType.ARROW):
                        self.advance()
                        body = self.expression()
                        return Lambda([], body)
                    else:
                        # just empty grouping ()
                        return Literal(None)
                else:
                    # try collect ids
                    first = self.peek()
                    # peek ahead to see if it's lambda pattern
                    temp_pos = self.current
                    temp_params = []
                    ok = True
                    while True:
                        if self.check(TokenType.IDENTIFIER):
                            temp_params.append(self.advance().lexeme)
                            if self.match(TokenType.COMMA):
                                continue
                            elif self.check(TokenType.RPAREN):
                                self.advance()
                                if self.check(TokenType.ARROW):
                                    is_lambda_params = True
                                break
                            else:
                                ok = False
                                break
                        else:
                            ok = False
                            break
                    if is_lambda_params and ok:
                        self.advance() # =>
                        body = self.expression()
                        return Lambda(temp_params, body)
                    else:
                        # restore
                        self.current = saved
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return Grouping(expr)
        if self.match(TokenType.LBRACK):
            elems = []
            if not self.check(TokenType.RBRACK):
                while True:
                    elems.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACK, "Expected ']' after list")
            return ListLiteral(elems)
        if self.match(TokenType.LBRACE):
            # dict literal: { key: value, ... } or empty
            pairs = []
            if not self.check(TokenType.RBRACE):
                while True:
                    # key
                    if self.check(TokenType.IDENTIFIER):
                        key = self.advance().lexeme
                    elif self.check(TokenType.STRING):
                        key = self.advance().literal
                    else:
                        raise ParseError(f"[{self.filename}:{self.peek().line}:{self.peek().col}] Expected key in dict")
                    self.consume(TokenType.COLON, "Expected ':' after key")
                    val = self.expression()
                    pairs.append((key, val))
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACE, "Expected '}' after dict")
            return DictLiteral(pairs)

        tok = self.peek()
        raise ParseError(f"[{self.filename}:{tok.line}:{tok.col}] Unexpected token '{tok.lexeme}'")

def parse(tokens, filename="<input>"):
    return Parser(tokens, filename).parse()
