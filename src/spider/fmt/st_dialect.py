"""
SpiderLang second-language dialect (.st).

The .st recovery/image files are NOT a re-encoding of the traditional .mk
makefiles. They speak their own Spider-native vocabulary: image blocks, kit
(ramdisk fragments), patch rules, head (header) options, multitool — tokens a
makefile never had. These tokens are first-class in the lexer/parser, so a .st
file is genuinely its own language, with its own naming and its own rules.
"""

import re

# .st-native keyword vocabulary (distinct from Android .mk variable names)
ST_KEYWORDS = {
    # image kinds
    "image", "boot", "recovery", "vendor_boot", "init_boot",
    # kit / ramdisk assembly
    "kit", "ramdisk", "fragment", "stage", "addon",
    # image header & overlay
    "head", "kernel", "dtbo", "dtb", "bootconfig", "acpio",
    # patching / tools (magisk is the hidden engine underneath)
    "patch", "magisk", "mtk", "sig", "sign", "vbmeta",
    # flags
    "feature", "flag",
    # partition layout
    "slot", "slotselect", "super", "dynamic",
    # builders
    "header", "pagesize", "base", "os", "board", "cmdline",
    "max_bytes", "type", "src", "vars", "owner",
}

# .st block headers that open a section
ST_BLOCKS = {"image", "kit", "head", "patch", "feat", "boot", "recovery",
             "vendor_boot", "init_boot", "ramdisk"}

# comment leaders allowed in .st (its own style, not make's '#')
ST_COMMENT_LEADERS = ("//", "#", ";")

# makefile-isms that should NOT appear in a well-formed .st (they belong to .mk)
MK_LEAKS = ("LOCAL_", "ifeq", "endif", "PRODUCT_", "BOARD_", "TARGET_",
            "$(call", "include ", "-include")


def is_st_keyword(word):
    return word.lower() in ST_KEYWORDS


def is_st_block(word):
    return word.lower() in ST_BLOCKS


def st_keywords():
    return sorted(ST_KEYWORDS)


def mk_leaks(text):
    """Return any makefile-isms leaked into a .st file (should be none)."""
    found = [l for l in MK_LEAKS if l in text]
    return found


def st_coverage(text):
    """How much of an image block body is .st-native vs unknown."""
    toks = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
    known = toks & ST_KEYWORDS
    return len(known), len(toks)


def classify(filename):
    """Is this a .st, .spt, .spider, or .mk file dialect?"""
    n = (filename or "").lower()
    if n.endswith(".st"):
        return "st"
    if n.endswith(".spt") or n.endswith(".spider"):
        return "spt"
    if n.endswith(".mk"):
        return "mk"
    return "unknown"


def st_render(block="image", name="recovery", fields=None):
    """Render a .st section from a plain dict — the second language's own syntax."""
    fields = fields or {}
    lines = [f'{block} "{name}" {{']
    for k, v in fields.items():
        if isinstance(v, list):
            lines.append(f"    {k}: [{', '.join(repr(str(x)) for x in v)}],")
        else:
            lines.append(f"    {k}: {str(v)!r},")
    lines.append("}")
    return "\n".join(lines)


def is_st_dialect(filename, text=None):
    """Best-effort: is this file written in the .st dialect?"""
    if classify(filename) != "st":
        return False
    if text:
        # present but should contain no leaked makefile-isms
        return not bool(mk_leaks(text))
    return True
