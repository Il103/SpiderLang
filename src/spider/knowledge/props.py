"""
SpiderLang Props knowledge — native understanding of Android .prop files.
system.prop / vendor.prop / product.prop / odm.prop / default.prop etc.
Like fstab and Soong, .prop files keep their own extension and grammar,
but Spider reads them natively — no shell, no make.
Grammar:
  # comment  or  ! comment
  key=value
  key = value   (spaces allowed)
  key:value     (rare)
  import /path/file.prop
Values are raw strings — may contain =, :, spaces. Keys are [A-Za-z0-9_.-]+
"""
import re
from pathlib import Path

PROP_KEY_RE = re.compile(r'^[A-Za-z0-9_.\-@]+$')
IMPORT_RE = re.compile(r'^\s*import\s+(.+)$')

def parse_prop(text):
    """Parse a .prop file text -> dict + ordered list + diagnostics."""
    props = {}
    ordered = []  # list of (key, value, line)
    issues = []   # list of (line, msg)
    imports = []
    for idx, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#') or line.startswith('!'):
            continue
        m = IMPORT_RE.match(line)
        if m:
            imports.append((m.group(1).strip(), idx))
            continue
        # find separator: first '=' or ':' or ' '
        sep = -1
        for ch in ('=', ':'):
            if ch in line:
                sep = line.index(ch)
                break
        if sep == -1:
            # maybe whitespace sep
            parts = line.split(None, 1)
            if len(parts) == 2:
                k, v = parts[0].strip(), parts[1].strip()
            else:
                issues.append((idx, f"no separator in '{raw.strip()}'"))
                continue
        else:
            k = line[:sep].strip()
            v = line[sep+1:].strip()
        if not k:
            issues.append((idx, 'empty key'))
            continue
        if not PROP_KEY_RE.match(k):
            # still accept but warn
            issues.append((idx, f"odd key '{k}'"))
        # strip optional quotes around value
        if len(v) >= 2 and ((v[0]=='"' and v[-1]=='"') or (v[0]=="'" and v[-1]=="'")):
            v = v[1:-1]
        # last wins (Android behavior)
        props[k] = v
        ordered.append((k, v, idx))
    return {"props": props, "ordered": ordered, "imports": imports, "issues": issues, "total": len(ordered)}

def analyze_file(path):
    p = Path(path)
    if not p.exists():
        return {"exists": False, "path": str(p)}
    text = p.read_text(encoding='utf-8', errors='replace')
    r = parse_prop(text)
    r["exists"] = True
    r["path"] = str(p)
    r["filename"] = p.name
    return r

def analyze_many(paths):
    out = {}
    for fp in paths:
        out[str(fp)] = analyze_file(fp)
    return out

# Known important props for a complete device tree
ESSENTIAL_PROPS = {
    "ro.hardware": "hardware platform (mt6789 etc)",
    "ro.board.platform": "board platform",
    "ro.build.product": "build product codename",
    "ro.build.device": "build device codename",
    "ro.product.device": "product device",
}

def check_props(props_dict):
    missing = [k for k in ESSENTIAL_PROPS if k not in props_dict]
    return {"missing": missing, "complete": not missing, "hints": {k: ESSENTIAL_PROPS[k] for k in missing}}
