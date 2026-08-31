"""
SpiderLang tools — native Android build tool knowledge baked into the language.
magiskboot is a hidden capability living inside the engine (never a CLI flag).
"""
from .magisk import peek_header, analyze, verify_sections

__all__ = ["peek_header", "analyze", "verify_sections"]
