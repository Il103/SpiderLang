"""
SpiderLang Soong knowledge — the language's native understanding of Android's
Soong / Blueprints build system (.bp files), so it can read, validate, and emit
the build rules that used to be painful Android.mk. No per-repo scripts.
"""

import re

# The Soong module types Spider understands natively, with the key properties
# each one commonly carries. This mirrors what actually appears in a real
# device/vendor tree.
SOONG_MODULES = {
    "cc_binary": {
        "srcs", "name", "defaults", "shared_libs", "static_libs", "include_dirs",
        "cflags", "cppflags", "ldflags", "header_libs", "init_rc", "stem",
        "owner", "vendor", "product_available", "recovery_available",
        "target", "arch", "soc_specific", "check_elf_files", "compile_multilib",
    },
    "cc_library": {
        "name", "srcs", "shared_libs", "static_libs", "header_libs", "export_include_dirs",
        "cflags", "cppflags", "vendor", "recovery_available", "proprietary", "stem",
    },
    "cc_library_static": {"name", "srcs", "static_libs", "header_libs", "cflags", "vendor", "recovery_available"},
    "cc_library_shared": {"name", "srcs", "shared_libs", "header_libs", "cflags", "vendor", "recovery_available"},
    "cc_defaults": {"name", "srcs", "shared_libs", "static_libs", "cflags", "cppflags", "ldflags", "include_dirs"},
    "filegroup": {"name", "srcs"},
    "prebuilt_etc": {"name", "src", "filename", "sub_dir", "vendor"},
    "prebuilt_usr_share_init": {"name", "src"},
    "init_rc": {"name", "srcs", "vendor"},
    "kernel_bootconfig": {"name", "src"},
    "subsystem_soong_namespace": {"domain", "install"},
    "fstab": {"name", "srcs", "vendor"},
    "ramdisk_available": set(),  # a property, not a module — kept for completeness
}

# Property authority: which recoveries/Soong flags are common vs optional.
# "hard" = expected for a complete module; "soft" = nice to have.
SOONG_HARD_PROPERTIES = {"name", "srcs"}


def parse_bp(text):
    """Parse a .bp (Blueprints) file into a list of module dicts."""
    modules = []
    pos = 0
    n = len(text)
    while pos < n:
        m = re.search(r"([a-z_0-9]+)\s*\{", text[pos:])
        if not m:
            break
        start = pos + m.end()
        name = m.group(1)
        # find matching close brace (naive brace counter)
        depth = 1
        i = start
        while i < n and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start:i - 1]
        modules.append({"type": name, "body": body})
        pos = i
    return modules


def parse_properties(body):
    """Extract key: value pairs from a module body (best effort)."""
    props = {}
    for m in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*("(?:\\.|[^"])*"|\[[^\]]*\]|[A-Za-z0-9_\.\-\/]+)', body):
        props[m.group(1)] = m.group(2).strip('"')
    return props


def analyze_file(text):
    """Understand a whole .bp file: modules + completeness notes."""
    modules = []
    for mod in parse_bp(text):
        props = parse_properties(mod["body"])
        mtype = mod["type"]
        known = mtype in SOONG_MODULES
        missing = []
        if mtype in SOONG_MODULES:
            missing = [p for p in SOONG_MODULES[mtype]
                       if p in SOONG_HARD_PROPERTIES and p not in props]
        modules.append({
            "type": mtype,
            "known": known,
            "props": props,
            "missing": missing,
            "complete": not missing and known,
        })
    return modules


def counts(modules):
    """Aggregate counts + a completeness verdict for a .bp file."""
    total = len(modules)
    complete = sum(1 for m in modules if m["complete"])
    known = sum(1 for m in modules if m["known"])
    missing = sum(len(m["missing"]) for m in modules)
    return {
        "total": total, "known": known, "complete": complete,
        "incomplete": total - complete, "missing_props": missing,
        "verdict": "OK" if total and complete == total else
                   ("partial" if complete else "empty"),
    }


def render_summary(modules):
    lines = []
    for m in modules:
        flag = "OK " if m["complete"] else ("?  " if m["known"] else "!  ")
        notes = f"  missing: {', '.join(m['missing'])}" if m["missing"] else ""
        lines.append(f"{flag} {m['type']}{notes}")
    return "\n".join(lines)
