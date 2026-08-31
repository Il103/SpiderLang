"""
SpiderLang tools — Android build tool knowledge baked into the language.
"""
from .magisk import peek_header, analyze, verify_sections

__all__ = ["peek_header", "analyze", "verify_sections"]
