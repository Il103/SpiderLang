"""
SpiderLang — the chip host.

The chip is the native C++ binary that does the real work (Android.tm parsing,
boot-image header verification, and the bundled magiskboot). This module finds
or builds the native binary, calls it, and returns its output as plain values.

If the native binary cannot be built/run, every function degrades gracefully
and reports an error instead of re-implementing the logic in Python.
"""

import os
import shutil
import subprocess
import sys

__all__ = ["chip_binary", "chip_check_image", "chip_tm", "chip_available"]


def _package_root():
    # src/spider/chip.py -> src/ -> repo root (parent of src)
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def _chip_bin_path():
    root = _package_root()
    for cand in (
        os.path.join(root, "native", "build", "spider"),
        os.path.join(root, "native", "spider"),
    ):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def chip_binary():
    """Return the (absolute) chip binary path, building it if necessary."""
    path = _chip_bin_path()
    if path:
        return path
    root = _package_root()
    native = os.path.join(root, "native")
    if not os.path.exists(os.path.join(native, "Makefile")):
        return None
    # try to build it, quietly
    try:
        subprocess.run(
            ["make", "-C", native], check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return _chip_bin_path()


def chip_available():
    """True if the native chip is usable right now."""
    return chip_binary() is not None


def _run(args):
    """Run the chip binary with args; return (rc, stdout)."""
    path = chip_binary()
    if not path:
        return None, ""
    try:
        p = subprocess.run(
            [path] + args,
            capture_output=True, text=True, timeout=60,
            cwd=os.path.dirname(path),
        )
        return p.returncode, p.stdout
    except (subprocess.SubprocessError, OSError):
        return None, ""


def chip_check_image(img_path, expected_size=None):
    """Ask the chip to verify a boot/recovery image header.

    Returns a dict with 'magic', 'header_version', 'page_size', 'os',
    'truncated' and a 'valid' flag, or None if the chip is unavailable.
    """
    args = ["check", img_path]
    if expected_size:
        args.append(str(expected_size))
    rc, out = _run(args)
    if out is None:
        return None
    result = {
        "magic": None, "header_version": None, "page_size": None,
        "os": None, "truncated": None, "valid": False,
        "native": True, "raw": out.strip(),
    }
    for line in out.splitlines():
        line = line.strip()
        if "magic ANDROID!" in line:
            result["magic"] = "ANDROID!"
        low = line.lower()
        if "header v" in low:
            part = line.split("header v")
            if len(part) > 1:
                try:
                    result["header_version"] = int(part[1].split()[0])
                except ValueError:
                    pass
        if "page_size" in low:
            part = line.split("page_size")
            if len(part) > 1:
                try:
                    result["page_size"] = int(part[1].split()[0])
                except ValueError:
                    pass
        if "os " in low and "." in line:
            import re
            m = re.search(r"\b(\d+\.\d+\.\d+)\b", line)
            if m:
                result["os"] = m.group(1)
        if "kernel " in low:
            import re
            m = re.search(r"kernel (\d+) ramdisk (\d+)", line)
            if m:
                result["kernel_bytes"] = int(m.group(1))
                result["ramdisk_bytes"] = int(m.group(2))
        if "truncated" in low:
            result["truncated"] = "looks truncated" in low
    # derived completeness fields (matching the portable parser's contract)
    result["kernel_bytes"] = result.get("kernel_bytes", 0) or 0
    result["ramdisk_bytes"] = result.get("ramdisk_bytes", 0) or 0
    result["valid"] = bool(result["magic"]) and (result["truncated"] is not True)
    return result


def chip_tm(path):
    """Ask the chip to parse + validate an Android.tm file.

    Returns (modules, issues) where issues is a list of (tag, message) tuples,
    or (None, None) if the chip is unavailable.
    """
    rc, out = _run(["tm", path])
    if out is None:
        return None, None
    modules = None
    issues = []
    for line in out.splitlines():
        s = line.strip()
        if "->" in s and "module(s)" in s:
            import re
            m = re.search(r"(\d+) module", s)
            if m:
                modules = int(m.group(1))
        if s.startswith("[") and "] " in s:
            tag, _, msg = s[1:].partition("]")
            issues.append((tag.strip(), msg.strip()))
    return modules, issues
