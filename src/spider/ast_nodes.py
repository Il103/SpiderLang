"""
SpiderLang AST — كل النودز مبنية من الصفر
"""
from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class Program:
    statements: List[Any]

# Statements
@dataclass
class LetStmt:
    name: str
    value: Any
    line: int; col: int

@dataclass
class FuncStmt:
    name: str
    params: List[str]
    body: Any  # Block
    line: int; col: int

@dataclass
class BoardStmt:
    # board { arch: "arm64", ... }
    properties: dict  # name -> expr, but nested dicts
    fields: List[tuple]  # list of (key, value)
    line: int; col: int

@dataclass
class UseStmt:
    lang: str
    path: str
    alias: str
    line: int; col: int

@dataclass
class IfStmt:
    condition: Any
    then_branch: Any
    else_branch: Optional[Any]
    line: int; col: int

@dataclass
class ReturnStmt:
    value: Optional[Any]
    line: int; col: int

@dataclass
class PrintStmt:
    value: Any
    line: int; col: int

@dataclass
class ExprStmt:
    expr: Any
    line: int; col: int

@dataclass
class Block:
    statements: List[Any]

# Expressions
@dataclass
class Assign:
    name: str
    value: Any

@dataclass
class Binary:
    left: Any
    op: str
    right: Any

@dataclass
class Unary:
    op: str
    right: Any

@dataclass
class Call:
    callee: Any
    args: List[Any]

@dataclass
class Get:
    obj: Any
    name: str  # property

@dataclass
class Index:
    obj: Any
    index: Any

@dataclass
class Literal:
    value: Any

@dataclass
class Variable:
    name: str

@dataclass
class ListLiteral:
    elements: List[Any]

@dataclass
class DictLiteral:
    pairs: List[tuple]  # (key, value)

@dataclass
class Lambda:
    params: List[str]
    body: Any

@dataclass
class Grouping:
    expr: Any
