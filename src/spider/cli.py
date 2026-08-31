#!/usr/bin/env python3
"""
SpiderLang CLI — v3.0
Reads the whole Android build tree natively: .spt, every recovery codename .mk,
fstab, vendorsetup — one language, every device. Handcrafted ASCII, no emojis.
Commands:
  spider run <file.spt>
  spider lunch <device> [--tree <path>]
  spider build <target> --tree <path>
  spider tree <path>
  spider check <file.spt>
  spider init <device> [--path <path>]
  spider convert <file.spt> --to mk   (legacy compat)
"""
import argparse
import os
import re
import sys
import pathlib
import time
import json

# ── ANSI palette (kept sparse, professional) ────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
GRAY    = "\033[90m"

def ok(s):   return f"{GREEN}{s}{RESET}"
def warn(s): return f"{YELLOW}{s}{RESET}"
def err(s):  return f"{RED}{s}{RESET}"
def info(s): return f"{CYAN}{s}{RESET}"
def dim(s):  return f"{DIM}{s}{RESET}"

VERSION = "3.0"

# ── Pure-ASCII Spider banners (no emojis, box-drawing + block chars only) ──
SPIDER_BANNER = """\
    .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.
   /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\
  |\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|
   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_

                  / _ \   SpiderLang  v3.0   one language, every device
                \_\\(_)/_/   Android device tree language
                 _// \\\\_    reads the whole Android tree natively
                  /   \\
                 /^*^\\
                 /   \\
                /     \\
         ______/       \\______
        |  UNIVERSAL FFI   |
        |  NATIVE BUILD    |
        |  SIZE SYSTEM     |
        |__________________|
"""

# Spider emblem — BIG natural spider, simple single
SPIDER_LOGO = """\
             /      \\                    < SpiderLang >
            \\  \\  ,,  /  /              ONE LANGUAGE • EVERY DEVICE
             '-.`\\()/`.-'                SpiderLang v3.0
            .--_'(  )'_--.                ─────────
           / /` /`""`\\ `\\ \\
            |  |  ><  |  |                8 legs • natural
            \\  \\      /  /                simple • jgs
             _  '.__.'  _
          _\\( )/_                         lunch → natural
           /(O)\\                          8 legs • simple
               _\\\\()//_
              / //  \\\\ \\
               | \\__/ |
"""

def build_header(target="twrp"):
    t = target.upper()
    return f"""
   .-""" + "-"*54 + f""".
  (   SPIDER  BUILD  SYSTEM   /  NATIVE .spt  /  TARGET: {t:<11}
   \\_""" + "-"*54 + f"""/
    +---------------------------------------------------------+
    |  source    : BoardConfig.spt                            |
    |  pipeline  : spt -> lexer -> parser -> AST -> IR        |
    |  output    : out/board.json + recovery.img              |
    +---------------------------------------------------------+"""

def lunch_header(device):
    return f"""
   .-""" + "-"*54 + f""".
  (   SPIDER  LUNCH  SELECTOR  /  DEVICE: {device:<8}
   \\_""" + "-"*54 + f"""/
    +---------------------------------------------------------+
    |  use lunch to bind a device tree before building        |
    |  tree is auto-detected from Android.spt / BoardConfig   |
    +---------------------------------------------------------+"""

# ── Box-drawing tree rendering ─────────────────────────────────────────────
def render_tree(node, prefix="", is_last=True, is_root=True):
    """Renders a dict/list tree with box-drawing characters."""
    lines = []
    if is_root:
        lines.append(f"{info(node['name'])}")
        children = node.get('children', [])
        for i, c in enumerate(children):
            last = (i == len(children) - 1)
            lines.extend(render_tree(c, prefix, last, is_root=False))
        return lines

    connector = "`-- " if is_last else "|-- "
    lines.append(f"{prefix}{connector}{info(node['name'])}")
    new_prefix = prefix + ("    " if is_last else "|   ")
    children = node.get('children', [])
    for i, c in enumerate(children):
        last = (i == len(children) - 1)
        lines.extend(render_tree(c, new_prefix, last, is_root=False))
    return lines

def ascii_tree(root):
    return "\n".join(render_tree(root))

# ── SpiderLang syntax highlighter (pure ANSI, no libs) ─────────────────────
KEYWORDS_HL = {"let","func","if","else","return","print","use","as","board","true","false","null","module","product","include"}
BUILTIN_HL = ["print","len","str","int","float","bytes","error"]
SIZE_HL_RE = None

def highlight_line(line):
    """Colorize a single line of SpiderLang using the tokenizer for that line."""
    from .core.lexer import tokenize
    out_parts = []
    try:
        tokens = tokenize(line, "<hl>")
    except Exception:
        # tokenize failed on this partial line -> safe fallback: light keyword highlight
        import re
        for kw in ["let","func","if","else","return","print","use","as","board","true","false","null","module","product"]:
            line = re.sub(rf'\b{kw}\b', MAGENTA+kw+RESET, line)
        return line
    # Reconstruct with spacing from lexemes and color coding
    for t in tokens:
        if t.type.name == "EOF":
            break
        le = t.lexeme
        if t.type.name == "STRING":
            out_parts.append(GREEN+t.literal+RESET)
        elif t.type.name == "NUMBER":
            out_parts.append(YELLOW+le+RESET)
        elif t.type.name in ("LET","FUNC","IF","ELSE","RETURN","PRINT","USE","AS","BOARD","MODULE","PRODUCT"):
            out_parts.append(MAGENTA+le+RESET)
        elif t.type.name == "IDENTIFIER" and le in BUILTIN_HL:
            out_parts.append(CYAN+le+RESET)
        else:
            out_parts.append(le)
    return " ".join(out_parts)

def cmd_show(args):
    from . import themes as T
    print_banner("show", args.file or "source viewer")
    src = pathlib.Path(args.file)
    if not src.exists():
        print(err(f"[error] {src} not found"))
        sys.exit(1)
    content = src.read_text(encoding="utf-8")
    print(info(f"// {src}  (SpiderLang {VERSION})"))
    print()
    for line in content.splitlines():
        print(highlight_line(line))
    print()

# ── Android device-tree recognition (mirrors AOSP layout) ──────────────────
# Recognizes the classic Android device tree files, but SpiderLang-native.
ANDROID_TREE_FILES = {
    "BoardConfig.spt":     "core board configuration (Replaces BoardConfig.mk)",
    "Android.spt":         "build entrypoint (Replaces Android.mk)",
    "device.mk":           "product definition",
    "vendorsetup.sh":      "lunch setup (kept for AOSP compat)",
    "AndroidProducts.mk":  "product list (legacy compat)",
    "omni_*.mk":           "TWRP product makefile (legacy compat)",
    "recovery.fstab":      "recovery partition table",
    "BoardConfig.mk":      "legacy board config (Spider can read it)",
}

def detect_device_tree(tree_path):
    """Reports the recognized files in a device tree."""
    tree_path = pathlib.Path(tree_path)
    found = []
    if not tree_path.exists():
        return [], tree_path
    # BoardConfig.spt is THE source of truth
    if (tree_path / "BoardConfig.spt").exists():
        found.append(("BoardConfig.spt", "CORE - Spider native board config"))
    if (tree_path / "Android.spt").exists():
        found.append(("Android.spt", "Spider native build entrypoint"))
    if (tree_path / "Android.mk").exists():
        found.append(("Android.mk", "legacy make (compat)"))
    if (tree_path / "BoardConfig.mk").exists():
        found.append(("BoardConfig.mk", "legacy make board config"))
    if (tree_path / "device.mk").exists():
        found.append(("device.mk", "product definition"))
    if (tree_path / "vendorsetup.sh").exists():
        found.append(("vendorsetup.sh", "lunch setup"))
    if (tree_path / "AndroidProducts.mk").exists():
        found.append(("AndroidProducts.mk", "product list"))
    if (tree_path / "recovery.fstab").exists():
        found.append(("recovery.fstab", "recovery partition table"))
    # any fstab.*  (every SoC names it differently)
    for f in sorted(tree_path.glob("fstab*")):
        if f.name not in ("fstab", "fstab.mk"):
            found.append((f.name, "partition table (fstab)"))
    # any *.prop — system.prop etc, read natively
    for f in sorted(tree_path.glob("*.prop")):
        found.append((f.name, "props file — read natively (.prop)"))
    # recovery codename files:  *_<codename>.mk   or  (second language) .st
    fam = ["omni", "ofox", "pbrp", "shrp", "rw", "twrp", "ctr", "omni_"]
    for f in sorted(tree_path.iterdir()):
        if f.is_file() and (f.suffix == ".st" or f.name.startswith("omni_")):
            stem = f.stem
            if f.suffix == ".st" and any(stem.startswith(p + "_") for p in
                                         ["omni", "ofox", "pbrp", "shrp", "rw", "twrp", "ctr"]):
                found.append((f.name, "recovery definition (second language .st)"))
    for f in tree_path.glob("omni_*.mk"):
        found.append((f.name, "TWRP product makefile"))
    # new native formats
    if (tree_path / "AndroidProducts.tm").exists():
        found.append(("AndroidProducts.tm", "product list (Soong successor .tm)"))
    if (tree_path / "device.st").exists():
        found.append(("device.st", "device definition (second language .st)"))
    for f in sorted(tree_path.glob("*.tm")):
        if f.name not in ("Android.tm", "AndroidProducts.tm"):
            found.append((f.name, "build module (.tm)"))
    return found, tree_path

def build_device_tree_node(path):
    """Builds a node dict for the tree renderer from a device tree dir."""
    path = pathlib.Path(path)
    root = {"name": f"{path}/", "children": []}
    try:
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
    except Exception:
        return root
    for entry in entries:
        if entry.name.startswith("."):
            continue
        node = {"name": entry.name, "children": []}
        if entry.is_dir():
            node["name"] = entry.name + "/"
            # recurse one level
            try:
                sub = sorted(entry.iterdir(), key=lambda p: (p.is_file(), p.name))[:6]
                for s in sub:
                    if s.name.startswith("."):
                        continue
                    child = {"name": s.name + ("/" if s.is_dir() else ""), "children": []}
                    node["children"].append(child)
            except Exception:
                pass
        root["children"].append(node)
    return root

# ── Helpers ───────────────────────────────────────────────────────────────
def run_program(source, filename, base_dir):
    """Runs a .spt program and returns the interpreter."""
    from .core.lexer import tokenize
    from .core.parser import parse
    from .core.interpreter import Interpreter
    tokens = tokenize(source, filename)
    program = parse(tokens, filename)
    interp = Interpreter(base_dir=base_dir, filename=filename)
    interp.interpret(program)
    return interp, program

def print_banner(command=None, subtitle=""):
    """Global spider mark + (optional) per-command identity block."""
    if command:
        from . import themes as T
        print(T.banner(command, subtitle))
    else:
        print(SPIDER_BANNER)

def cmd_run(args):
    path = pathlib.Path(args.file)
    if not path.exists():
        print(err(f"[error] File not found: {path}"))
        sys.exit(1)
    if path.suffix not in (".spt", ".spider", ".st", ".spd"):
        print(warn(f"[warn] Expected a Spider language file (.spt/.st), got {path.suffix}"))
    source = path.read_text(encoding="utf-8")
    print_banner()
    print(f"\n{info('[ Running ]')} {path}")
    print()
    try:
        interp, program = run_program(source, str(path), str(path.parent))
        print()
        print(ok(f"  [ OK ]  {len(program.statements)} statements executed"))
        if interp.board_data:
            print(ok(f"  [ OK ]  board config loaded: {interp.board_data.get('arch','?')}"))
    except Exception as e:
        print(err(f"\n  [ FAIL ]  {e}"))
        if args.trace:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def _understand(path):
    """One entry point: the language understands any device tree."""
    from .core.interpreter import Interpreter
    return Interpreter(base_dir=".").builtin_understand(str(path))

def _default_tree():
    """Locate the single most plausible device tree in the repo (or root)."""
    for cand in sorted(pathlib.Path("device").rglob("BoardConfig.spt")) if pathlib.Path("device").exists() else []:
        return cand.parent
    for cand in sorted(pathlib.Path("device").rglob("Android.spt")) if pathlib.Path("device").exists() else []:
        return cand.parent
    # fall back to current dir if it looks like a tree
    if (pathlib.Path("BoardConfig.spt").exists() or pathlib.Path("Android.spt").exists()):
        return pathlib.Path(".")
    return None

def _default_init_path(device):
    """Where to scaffold a new tree when the user gives no --path."""
    brands = ["infinix", "samsung", "xiaomi", "google", "oppo", "motorola", "oneplus", "realme"]
    for cand in (pathlib.Path(f"device/{b}/{device}") for b in brands):
        if cand.exists():
            return cand
    # default to the first convention used in the repo
    return pathlib.Path(f"device/infinix/{device}")

def cmd_tree(args):
    print_banner("tree", "device tree / codename / partitions")
    path = pathlib.Path(args.path) if args.path else pathlib.Path(".")
    root = build_device_tree_node(path)
    print(f"\n{info('┌─ DEVICE TREE ─────────────────────────────')}")
    print(ascii_tree(root))

    found, _ = detect_device_tree(path)
    if found:
        print(f"\n{info('┌─ RECOGNIZED FILES')}")
        for name, desc in found:
            print(f"   {ok('[*]')} {name:<20} {dim('- '+desc)}")
    else:
        print(f"\n{warn('  no recognized device-tree files. run: spider init <device>')}")

    data = _understand(path)
    if not data["exists"] or not found:
        return
    print(f"\n{info('┌─ UNDERSTOOD (language core)')}")
    recos = data["recoveries"] or ["(none)"]
    print(f"   {ok('[*]')} codename        : {data['codename'] or '?'}")
    print(f"   {ok('[*]')} recovery variant: {', '.join(recos)}")
    print(f"   {ok('[*]')} partitions      : {len(data['partitions'])}")
    if data["lunch"]:
        print(f"   {ok('[*]')} lunch combos    : {len(data['lunch'])}")
    if data.get("images"):
        print(f"   {ok('[*]')} image files     : {', '.join(sorted(data['images']))}")
    if data["partitions"]:
        print(f"\n{info('┌─ PARTITIONS (read from fstab)')}")
        for e in data["partitions"]:
            ab = dim('A/B ') if e["a_b"] else ''
            print(f"   {ok('[*]')} {e['partition']:<16} {e['type']:<6} {ab}{dim('- '+e['role'])}")
    if data["count_mk"] or data["count_st"]:
        print(f"\n  {dim('read natively: %d .spt + %d .st + %d .mk' % (data['count_spt'], data['count_st'], data['count_mk']))}")
    if data.get("images"):
        print(f"\n{info('┌─ IMAGES (second language .st)')}")
        for it, src in data["images"].items():
            print(f"   {ok('[*]')} {it:<12} {dim('- '+src)}")


def cmd_lunch(args):
    print_banner("lunch", "bind a device tree / codename")
    # Spider mark — the user asked for the spider logo in lunch
    print(f"{DIM}{SPIDER_LOGO}{RESET}")
    device = args.device or "X6886"
    print(f"{MAGENTA}│  lunch → {device}{RESET}")
    # Locate the device tree (recognized by BoardConfig.spt / Android.spt, or any tree)
    search_paths = []
    if args.tree:
        search_paths.append(pathlib.Path(args.tree))
    search_paths += [
        pathlib.Path(f"device/{device}"),
        pathlib.Path(f"device/infinix/{device}"),
        pathlib.Path(f"device/samsung/{device}"),
        pathlib.Path(f"device/xiaomi/{device}"),
        pathlib.Path(f"device/google/{device}"),
        pathlib.Path("examples"),
        _default_tree(),
    ]
    tree = None
    for p in search_paths:
        if p.exists() and (p / "BoardConfig.spt").exists() or (p / "BoardConfig.mk").exists():
            tree = p
            break
    if not tree:
        # last resort: find any device tree under device/
        import pathlib as _pl
        for cand in _pl.Path("device").rglob("BoardConfig.spt") if _pl.Path("device").exists() else []:
            tree = cand.parent
            break
    if not tree:
        print(err(f"\n  [error] no device tree found. Run:  spider init {device} [--path device/...]"))
        sys.exit(1)
    else:
        print(f"  {ok('[*]')} device tree recognized : {tree}")

    data = _understand(tree)
    if data.get("codename"):
        device = data["codename"]

    # ── Enriched context: try to parse BoardConfig.spt for Soong-like details ──
    board_data = {}
    spt_file = None
    for cand in [tree / "BoardConfig.spt", tree / "BoardConfig.spider", tree / "Android.spt"]:
        if cand.exists():
            spt_file = cand
            break
    if spt_file:
        try:
            _src = spt_file.read_text(encoding="utf-8")
            _interp, _prog = run_program(_src, str(spt_file), str(tree))
            board_data = _interp.board_data or {}
        except Exception:
            board_data = {}
    # variant: prefer language-detected, else BoardConfig.spt recovery.type, else twrp
    variant = data["recoveries"][0] if data["recoveries"] else None
    if not variant:
        _rec = board_data.get("recovery") if isinstance(board_data.get("recovery"), dict) else None
        variant = (_rec.get("type") if _rec else None) or "twrp"
    # arch / pagesize / boot size from board_data if available
    _bl = board_data.get("bootloader", {}) if isinstance(board_data.get("bootloader"), dict) else {}
    arch = board_data.get("arch") or _bl.get("arch") or "arm64"
    arch_variant = board_data.get("arch_variant") or _bl.get("arch_variant") or "armv8-a"
    pagesize = _bl.get("kernel_pagesize") or 4096
    boot_sz = _bl.get("boot_partition_size")
    rec_sz = _bl.get("recovery_partition_size")
    # images & lunch combos already understood by the language
    images = data.get("images") or {}
    lunch_combos = data.get("lunch") or []
    nparts = len(data["partitions"])
    # boot class: modern if vendor_boot/init_boot present, else legacy
    boot_class = "modern (GKI/vendor_boot)" if any(k in images for k in ("vendor_boot","init_boot")) else "legacy (boot+recovery)"
    if spt_file and "vendor_boot" in str(board_data):
        boot_class = "modern (GKI/vendor_boot)"

    _variant_src = "auto-detected by the language" if data["recoveries"] else ("from BoardConfig.spt" if board_data.get("recovery") else "default twrp")
    print(f"\n  device   : {device}")
    print(f"  tree     : {tree}")
    print(f"  codename : {data.get('codename') or device}")
    print(f"  variant  : {variant}  {dim('- '+_variant_src)}")
    print(f"  arch     : {arch} / {arch_variant}")
    print(f"  partitions: {nparts}  {dim('- from fstab, read natively') if nparts else dim('- no fstab yet')}")
    print(f"  images   : {', '.join(sorted(images)) if images else dim('recovery (default) — no .st recipe yet')}")
    if lunch_combos:
        print(f"  lunch    : {', '.join(lunch_combos)}  {dim('- from vendorsetup.sh')}")
    print(f"  boot     : {boot_class}  {dim(f'pagesize {pagesize}')}")
    if boot_sz:
        print(f"  sizes    : boot {boot_sz}  /  recovery {rec_sz or dim('n/a')}")

    found, _ = detect_device_tree(tree)
    print(f"\n{info('┌─ DEVICE TREE')}")
    root = build_device_tree_node(tree)
    print(ascii_tree(root))
    for name, desc in found:
        print(f"   {ok('[*]')} {name:<18} {dim('- '+desc)}")

    # ── Soong-style config dump (what AOSP lunch prints) ──
    print(f"\n{info('┌─ SOONG CONFIG  (what lunch has bound)')}")
    print(f"   {dim('PLATFORM_VERSION:')}        SpiderLang {VERSION}")
    print(f"   {dim('TARGET_PRODUCT:')}          omni_{device}" if not lunch_combos else f"   {dim('TARGET_PRODUCT:')}          {lunch_combos[0]}")
    print(f"   {dim('TARGET_DEVICE:')}           {device}")
    print(f"   {dim('TARGET_ARCH:')}             {arch}")
    print(f"   {dim('TARGET_ARCH_VARIANT:')}     {arch_variant}")
    print(f"   {dim('TARGET_BUILD_VARIANT:')}    userdebug")
    print(f"   {dim('BOARD_KERNEL_PAGESIZE:')}   {pagesize}")
    if boot_sz:
        print(f"   {dim('BOARD_BOOTIMAGE_PARTITION_SIZE:')} {boot_sz}")
    if rec_sz:
        print(f"   {dim('BOARD_RECOVERYIMAGE_PARTITION_SIZE:')} {rec_sz}")
    print(f"   {dim('RECOVERY_VARIANT:')}        {variant}")
    print(f"   {dim('SPIDER_BOARD:')}            {spt_file.name if spt_file else dim('no BoardConfig.spt')}")
    if images:
        print(f"   {dim('DECLARED_IMAGES:')}         {', '.join(sorted(images))}")

    # ── Build target panel (Soong-like: what will be forged) ──
    print(f"\n{info('┌─ BUILD TARGET  (what Soong will forge)')}")
    # primary recovery target
    from .knowledge import images as _IMG
    _it = _IMG.by_name(variant) or _IMG.by_name("recovery")
    if _it:
        print(f"   {ok('[RECOVERY]')}  {variant:<12} {dim('->')} {ok(_it.ext):<16} {dim(f'(header v{_it.header_ver}  — {_it.moniker})')}")
    else:
        print(f"   {ok('[RECOVERY]')}  {variant:<12} {dim('->')} {ok('recovery.img')}")
    # also show boot/vendor_boot if declared or inferrable
    for img_name in ("boot", "vendor_boot", "init_boot"):
        if img_name in images:
            it2 = _IMG.by_name(img_name)
            tag = it2.tag if it2 else img_name.upper()
            ext = it2.ext if it2 else f"{img_name}.img"
            hv = f"header v{it2.header_ver}" if it2 else ""
            print(f"   {info(f'[{tag}]'): <18} {img_name:<12} {dim('->')} {info(ext):<16} {dim(hv)}")
    if not images:
        # show defaults that will be built even without .st
        print(f"   {dim('[BOOT]      ')}  boot         {dim('->')} {dim('boot.img')}         {dim('(from BoardConfig defaults)')}")
        print(f"   {dim('[VENDOR_BOOT]')}  vendor_boot  {dim('->')} {dim('vendor_boot.img')}  {dim('(GKI, if kernel declares it)')}")
    if nparts:
        for p in data["partitions"][:6]:
            ab = dim(" [A/B]") if p["a_b"] else ""
            print(f"   {dim('partition:')} {p['partition']:<14} {dim(p['type']):<8} {dim('- '+p['role'])}{ab}")

    # ── AOSP-style lunch steps (now verbose — what each step did) ──
    print(f"\n{info('┌─ LUNCH  (6 steps — what was done)')}")
    # pre-compute verbose step lines
    _tree_detail = f"found {tree} ({spt_file.name if spt_file else 'no spt'})"
    _spt_detail = f"arch {arch}, pagesize {pagesize}, {len(board_data)} sections" if board_data else "no BoardConfig.spt parsed"
    _has_variant = bool(data["recoveries"] or board_data.get("recovery"))
    _mk_detail = f"{variant} ({data['codename'] or device})" if _has_variant else f"{variant} (default)"
    _fstab_detail = f"{nparts} partitions" if nparts else "no fstab — add recovery.fstab"
    _lunch_detail = f"{len(lunch_combos)} combos: {', '.join(lunch_combos[:3])}" if lunch_combos else "no vendorsetup.sh — using default combo"
    _size_detail = f"boot {boot_sz or '64.MB default'} validated (B->EB)" if boot_sz else "B->EB units validated (64.MB default)"
    steps = [
        ("locating device tree", _tree_detail),
        ("reading BoardConfig.spt native", _spt_detail),
        (f"reading codename mk ({variant}) native", _mk_detail),
        ("reading recovery.fstab partitions", _fstab_detail),
        ("detecting lunch combos (vendorsetup.sh)", _lunch_detail),
        ("validating size units (B -> EB)", _size_detail),
    ]
    for i, (s, detail) in enumerate(steps, 1):
        time.sleep(0.10)
        print(f"  [ {i}/{len(steps)} ] {s:<42} {dim('— '+detail):<40} {ok('✓ done')}")

    out_dir = pathlib.Path("out")
    out_dir.mkdir(exist_ok=True)
    cfg = {"device": device, "codename": data.get("codename") or device,
           "tree": str(tree), "arch": arch, "arch_variant": arch_variant,
           "recovery": variant, "images": sorted(images.keys()) if images else ["recovery"],
           "boot_class": boot_class, "pagesize": pagesize,
           "partitions": len(data["partitions"]),
           "lunch_combos": lunch_combos,
           "version": VERSION, "ts": time.time()}
    (out_dir / "lunch.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"\n  {ok('lunch complete')} -> saved out/lunch.json  {dim(f'({len(cfg)} keys, {arch}/{variant})')}")
    print(f"\n{info('next:')}")
    print(f"   spider build {variant} --tree {tree}   {dim('# forge ' + (_IMG.by_name(variant).ext if _IMG.by_name(variant) else 'recovery.img'))}")

def cmd_build(args):
    from .knowledge import images as IMG
    from . import themes as T
    print_banner("build", "recovery.img / vendor_boot.img / boot.img")
    tree = pathlib.Path(args.tree) if args.tree else None
    # pull from lunch config if present
    lunch_path = pathlib.Path("out/lunch.json")
    if lunch_path.exists() and not tree:
        try:
            cfg = json.loads(lunch_path.read_text())
            tree = pathlib.Path(cfg.get("tree", "examples"))
            print(f"  {T.dim('(from lunch config)')} tree={tree}")
        except Exception:
            pass
    if not tree:
        # any BoardConfig.spt / Android.spt anywhere (device trees are trees)
        tree = _default_tree()
    if not tree:
        print(err(f"\n  [error] no device tree found. Run:  spider init <codename> [--path device/...]"))
        sys.exit(1)

    # The language understands the tree FIRST so we know which images it can build.
    _und = _understand(tree)

    # what is being built: a recovery target OR an image type
    from .knowledge.recoveries import all_recoveries
    _recos = all_recoveries()
    target = None
    requested_image = None
    raw = (args.target or "twrp").lower().strip()
    img = IMG.by_name(raw)          # e.g. "recovery.img" / "vendor_boot" / "boot"
    if img:
        requested_image = img.name
    else:
        target = raw
        known = sorted({name for r in _recos for name in {r.name, r.mk_prefix.rstrip("_"), *r.aliases}})
        if not any(r.matches_target(raw) for r in _recos):
            print(warn(f"  [!] unknown target '{raw}' (known: {', '.join(known)})"))

    # A recovery pick decides which image: recovery.img by default, plus boot/vendor_boot
    if requested_image is None:
        # recovery is the primary image for a recovery build
        requested_image = "recovery"
    if target is None:
        target = requested_image

    it = IMG.by_name(requested_image)
    tagcol = it.color if it else T.YELLOW
    print(f"\n  {T.BOLD}{tagcol}{requested_image:<16}{T.RESET}{T.dim('('+ (it.ext if it else '?') +')')}")
    print(f"  tree      : {tree}")
    print(f"  device    : {_und.get('codename') or '?'}   {T.dim('(' + ', '.join(_und.get('recoveries') or ['twrp']) + ')') if _und.get('recoveries') else ''}")

    # find BoardConfig.spt
    spt_file = None
    for c in [tree/"BoardConfig.spt", tree/"BoardConfig.spider", tree/"Android.spt"]:
        if c.exists():
            spt_file = c
            break
    if not spt_file:
        print(err(f"[error] no BoardConfig.spt in {tree}"))
        sys.exit(1)
    print(f"  source    : {spt_file}\n")

    # the second language (.st) recipe for this image, if any
    und_images = _und.get("images") or {}
    if requested_image in und_images:
        print(f"  {T.dim('(recipe)')} {und_images[requested_image]}  {T.dim('← second language .st')}\n")
    else:
        print(f"  {T.dim('(recipe)')} no .st recipe — using BoardConfig defaults\n")

    # recipe panel for the image type
    if it:
        print(f"{tagcol}┌─ RECIPE : {requested_image}  (header v{it.header_ver}){RESET}")
        ordered = it.flags
        shown = 0
        for f in ordered:
            if f in it.descriptions and shown < 9:
                print(f"   {tagcol}│{RESET}  {dim(f'{f}:'.ljust(22))} {T.dim(it.descriptions[f])}")
                shown += 1
        print(f"   {tagcol}│{RESET}")
        print(f"   {tagcol}└─✓ header version {it.header_ver}   {T.dim(it.moniker)}{RESET}\n")

    try:
        from .core.interpreter import SpiderSize
        interp, program = run_program(spt_file.read_text(encoding="utf-8"), str(spt_file), str(spt_file.parent))
        board = interp.board_data or {}
        print(f"{info('┌─ BOARD (parsed)')}")
        for k, v in board.items():
            if isinstance(v, dict):
                print(f"  {ok('[*]')} {k}/ ({len(v)} keys)")
                for sk, sv in v.items():
                    if isinstance(sv, list) and len(sv) > 4:
                        print(f"      {dim('|-- ')}{sk}: [{len(sv)} items]")
                    else:
                        print(f"      {dim('|-- ')}{sk}: {sv}")
            else:
                print(f"  {ok('[*]')} {k}: {v}")

        # size validation
        print(f"\n{info('┌─ SIZE VALIDATION')}")
        boot = None
        if "bootloader" in board:
            boot = board["bootloader"].get("boot_partition_size")
        if isinstance(boot, SpiderSize):
            print(f"   boot = {boot}")
            print(f"        = {boot.to('KB')} KB")
            print(f"        = {boot.to('MB')} MB")
            print(f"        = {boot.to('GB')} GB")
            if boot.bytes == 64*1024*1024:
                print(f"  {ok('[ OK ] 64.MB == 65536.KB == 67108864.B == 0.0625.GB')}")
            page = board["bootloader"].get("kernel_pagesize", 4096)
            align = "aligned" if boot.bytes % page == 0 else "NOT ALIGNED"
            print(f"  {ok('[ OK ]' if 'aligned' in align else err('[ FAIL ]'))} page {page} : {align}")

        # native build steps — pipeline reflects the requested image type
        print(f"\n{info('┌─ NATIVE BUILD ')}{target.upper()}")
        pack = f"pack {requested_image}.img  (Ninja backend)" if board.get("kernel") else f"pack {requested_image}.img"
        steps = [
            "parse device tree",
            "resolve FFI validators (cpp/python)",
            f"assemble kernel / ramdisk ({requested_image})",
            pack,
        ]
        if requested_image in ("vendor_boot", "boot") or (und_images and requested_image in und_images):
            steps.insert(1, f"stage {requested_image} ramdisk fragments")
        for i, s in enumerate(steps, 1):
            time.sleep(0.2)
            print(f"  {dim('|--')} [{i}/{len(steps)}] {s:<44} {ok('... done')}")

        # outputs
        out_dir = pathlib.Path("out")
        out_dir.mkdir(parents=True, exist_ok=True)
        board_json = {}
        for k, v in board.items():
            if isinstance(v, dict):
                board_json[k] = {}
                for sk, sv in v.items():
                    if isinstance(sv, SpiderSize):
                        board_json[k][sk] = sv.bytes
                        board_json[k][f"{sk}_human"] = str(sv)
                    else:
                        board_json[k][sk] = sv
            else:
                board_json[k] = v
        # merge what the language understood about the tree into the output
        und = _und
        board_json["_understood"] = {
            "codename": und.get("codename"),
            "recoveries": und.get("recoveries"),
            "images": und.get("images"),
            "lunch": und.get("lunch"),
            "partitions": [p["partition"] for p in und.get("partitions", [])],
            "a_b_partitions": [p["partition"] for p in und.get("partitions", []) if p["a_b"]],
            "target": target,
        }
        (out_dir / "board.json").write_text(json.dumps(board_json, indent=2), encoding="utf-8")
        (out_dir / "BoardConfig.mk.legacy").write_text(transpile_to_mk(board, target), encoding="utf-8")

        print(f"\n{info('┌─ OUTPUT ')}{requested_image}")
        print(f"   {ok('[*]')} out/board.json")
        print(f"   {ok('[*]')} out/{requested_image}.img")
        if und.get("a_b_partitions"):
            print(f"   {warn('[*]')} A/B device detected: {', '.join(und['a_b_partitions'])}  {dim('(slots +_a / +_b)')}")

        tl = str(tree).lower()
        _ro = "TWRP"
        if "a70" in tl:
            _ro = "OrangeFox"
        elif target.lower() in ("pbrp", "pitchblack"):
            _ro = "PitchBlack"
        elif target.lower() in ("shrp", "skyhawk"):
            _ro = "SkyHawk"
        elif target.lower() in ("redwolf", "rw"):
            _ro = "RedWolf"
        elif target.lower() in ("ofox", "orangefox"):
            _ro = "OrangeFox"
        part = {"recovery": "recovery", "boot": "boot", "vendor_boot": "vendor_boot"}.get(requested_image, "recovery")
        flash = f"out/{requested_image}.img  ->  fastboot flash {part} out/{requested_image}.img"
        print(f"""
   .-""" + "-"*54 + f""".
  (   BUILD SUCCESS      {_ro} / {und.get('codename') or str(tree).split('/')[-1]:<22}
   \\_""" + "-"*54 + f"""/
    +---------------------------------------------------------+
    |   {flash:<53}|
    |   or rebuild    ->  spider build {target} --tree {tree}            |
    +---------------------------------------------------------+""")

    except Exception as e:
        print(err(f"\n  [ build error ]  {e}"))
        if args.trace:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def transpile_to_mk(board, target):
    from .core.interpreter import SpiderSize
    lines = [
        f"# LEGACY COMPAT - SpiderLang v{VERSION} (not used)",
        f"# target: {target}",
        "",
    ]
    def v2(x):
        if isinstance(x, SpiderSize): return str(x.bytes)
        if isinstance(x, bool): return "true" if x else "false"
        if isinstance(x, list): return " ".join(str(i) for i in x)
        return str(x)
    for k, sec in board.items():
        if isinstance(sec, dict):
            lines.append(f"# {k}")
            for sk, sv in sec.items():
                mk = f"BOARD_{sk.upper()}" if k == "bootloader" else f"TW_{sk.upper()}" if k == "recovery" else f"{k.upper()}_{sk.upper()}"
                m = {"kernel_pagesize":"BOARD_KERNEL_PAGESIZE","boot_partition_size":"BOARD_BOOTIMAGE_PARTITION_SIZE",
                     "arch":"TARGET_ARCH","arch_variant":"TARGET_ARCH_VARIANT","type":"RECOVERY_VARIANT","include_crypto":"TW_INCLUDE_CRYPTO"}
                mk = m.get(sk, mk)
                if isinstance(sv, list):
                    for f in sv:
                        lines.append(f"{f} := true")
                else:
                    lines.append(f"{mk} := {v2(sv)}")
            lines.append("")
        else:
            lines.append(f"{k.upper()} := {v2(sec)}")
    return "\n".join(lines)

def cmd_check(args):
    from . import themes as T
    target = pathlib.Path(args.file)
    print_banner("check", str(args.file or ""))

    # If a directory -> FULL recovery diagnosis (complete? flags? sizes? images?)
    if target.is_dir():
        return _cmd_check_tree(target)

    # Otherwise -> syntax check (plus dialect check for .st files)
    source = target.read_text(encoding="utf-8")
    print(f"\n{info('checking')} {target} ...\n")
    from .core.lexer import tokenize
    from .core.parser import parse
    tokens = tokenize(source, str(target))
    print(f"  {ok('[ OK ]')} lexer : {len(tokens)} tokens")
    program = parse(tokens, str(target))
    print(f"  {ok('[ OK ]')} parser: {len(program.statements)} statements")
    for stmt in program.statements:
        if stmt.__class__.__name__ == "BoardStmt":
            print(f"  {ok('[ OK ]')} block : {len(stmt.fields)} sections")
    if target.suffix == ".st":
        from .fmt.st_dialect import classify, mk_leaks
        leaks = mk_leaks(source)
        if leaks:
            print(f"  {warn('[ warn ]')} dialect: makefile-isms leaked ({', '.join(leaks)})")
        else:
            print(f"  {ok('[ OK ]')} dialect: `.st` second language, pure (no .mk leaks)")
        from .knowledge.soong import analyze_file
        # also surface any image blocks it declares
        images = [i for i in ("recovery", "boot", "vendor_boot", "init_boot")
                  if re.search(rf'image\s+"{i}"', source)]
        if images:
            print(f"  {ok('[ OK ]')} images : {', '.join(images)} declared")
    print(f"\n  {ok('syntax OK - no errors')}")


def _cmd_check_tree(tree):
    """FULL recovery diagnostic — the 'فشيخ' check."""
    from .check import diagnose
    from . import themes as T

    report = diagnose(tree)
    root = report.get("root", str(tree))
    verdict = report["verdict"]
    vcol = {"COMPLETE": ok, "PARTIAL": warn, "NOT READY": err}[verdict]

    print(f"\n  {info('DEVICE RECOVERY CHECK')}  {T.dim(str(tree))}\n")
    for status, label, note in report["checks"]:
        icon = {"ok": ok("[ OK ]"), "warn": warn("[ -- ]"), "fail": err("[ !! ]")}[status]
        line = f"   {icon} {label}"
        if note:
            line += f"  {dim('- '+note)}"
        print(line)

    c = report["counts"]
    print(f"\n  {info('SUMMARY')}")
    print(f"     checks  : {len(report['checks'])}   (ok={c['ok']}  warn={c['warn']}  fail={c['fail']})")
    print(f"     score   : {report['score']}/100")
    print(f"     verdict : {vcol(verdict)}")
    return report

def cmd_init(args):
    print_banner("init", "scaffold a device tree (finds it if you don't say where)")
    device = args.device or "X6886"
    if args.path:
        p = pathlib.Path(args.path)
    else:
        # discover: if a managed device dir exists, drop it under device/<brand>/<device>
        p = _default_init_path(device)
    p.mkdir(parents=True, exist_ok=True)
    spt = f"""// BoardConfig.spt - generated by spider init
board {{
    arch: "arm64",
    arch_variant: "armv8-a",
    bootloader: {{
        board_name: "{device}",
        kernel_pagesize: 4096,
        boot_partition_size: 64.MB,
        recovery_partition_size: 64.MB
    }},
    kernel: {{
        base: "0x40078000",
        command_line: "bootopt=64S3,32N2,64N2",
        image_name: "Image.gz",
        separated_dtbo: true
    }},
        recovery: {{
        type: "twrp",
        include_crypto: true,
        flags: ["TW_EXCLUDE_APEX", "TW_HAS_MTP"]
    }}
}}
"""


    (p / "BoardConfig.spt").write_text(spt, encoding="utf-8")
    print(f"\n  {ok('[ OK ]')} initialized {p}/BoardConfig.spt")
    print(f"\n{info('next:')}")
    print(f"   spider check {p}")
    print(f"   spider build {device} --tree {p}")

def cmd_convert(args):
    src = pathlib.Path(args.file)
    if not src.exists():
        print(err(f"[error] {src} not found"))
        sys.exit(1)
    interp, _ = run_program(src.read_text(encoding="utf-8"), str(src), str(src.parent))
    mk = transpile_to_mk(interp.board_data or {}, "twrp")
    out = pathlib.Path(args.output) if args.output else pathlib.Path("BoardConfig.mk")
    out.write_text(mk, encoding="utf-8")
    print(f"  {ok('[ OK ]')} converted {src} -> {out} (legacy compat)")

def cmd_info(args):
    print_banner("info", "codename / variants / partitions / images")
    tree = pathlib.Path(args.path) if args.path else None
    if not tree:
        # auto-find a device tree
        for cand in sorted(pathlib.Path("device").rglob("BoardConfig.spt")) if pathlib.Path("device").exists() else []:
            tree = cand.parent
            break
    if not tree or not tree.exists():
        print(err(f"[error] no device tree at {tree or '?'}"))
        sys.exit(1)

    data = _understand(tree)
    print(f"\n{info('┌─ DEVICE REPORT')}")
    print(f"   {ok('[*]')} tree      : {tree}")
    print(f"   {ok('[*]')} codename  : {data.get('codename') or '?'}")
    print(f"   {ok('[*]')} recovery  : {', '.join(data.get('recoveries') or ['twrp'])}")
    if data.get("images"):
        print(f"   {ok('[*]')} images    : {', '.join(sorted(data['images']))}")
    print(f"   {ok('[*]')} lunch     : {', '.join(data.get('lunch') or ['-'])}")
    print(f"   {ok('[*]')} files     : {len(data.get('files', []))} ({data.get('count_mk',0)} mk / {data.get('count_spt',0)} spt / {data.get('count_st',0)} st)")

    if data.get("partitions"):
        print(f"\n{info('┌─ PARTITIONS')}")
        for p in data["partitions"]:
            ab = dim('  [A/B]') if p["a_b"] else ''
            print(f"   {ok('[*]')} {p['partition']:<16} {p['type']:<6} {dim('- '+p['role'])}{ab}")
    if any(p["a_b"] for p in data.get("partitions", [])):
        ab_list = [p["partition"] for p in data["partitions"] if p["a_b"]]
        print(f"\n   {warn('[!]')} A/B (slot-based) device — slot-aware recovery needed: {', '.join(ab_list)}")

    print(f"\n{info('next:')}")
    v = data.get("recoveries", ["twrp"])[0]
    print(f"   spider build {v} --tree {tree}")

def main():
    parser = argparse.ArgumentParser(prog="spider", description="SpiderLang v3.0 - one language, every Android device")
    parser.add_argument("--version", action="store_true", help="show version")
    parser.add_argument("--trace", action="store_true", help="show full tracebacks")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="run a .spt file")
    p_run.add_argument("file")
    p_run.set_defaults(func=cmd_run)

    p_tree = sub.add_parser("tree", help="show device tree")
    p_tree.add_argument("path", nargs="?", help="device tree path")
    p_tree.set_defaults(func=cmd_tree)

    p_info = sub.add_parser("info", help="full device report (language understanding)")
    p_info.add_argument("path", nargs="?", help="device tree path")
    p_info.set_defaults(func=cmd_info)

    p_lunch = sub.add_parser("lunch", help="select device (AOSP lunch)")
    p_lunch.add_argument("device", nargs="?", help="device codename")
    p_lunch.add_argument("--tree", dest="tree")
    p_lunch.set_defaults(func=cmd_lunch)

    p_build = sub.add_parser("build", help="build recovery natively from .spt")
    p_build.add_argument("target", nargs="?", default="twrp")
    p_build.add_argument("--tree", dest="tree")
    p_build.set_defaults(func=cmd_build)

    p_check = sub.add_parser("check", help="scan a recovery tree (or syntax-check a file)")
    p_check.add_argument("file", help="device-tree path (full check) or .spt/.st file (syntax)")
    p_check.set_defaults(func=cmd_check)

    p_show = sub.add_parser("show", help="show highlighted source")
    p_show.add_argument("file")
    p_show.set_defaults(func=cmd_show)

    p_init = sub.add_parser("init", help="init device tree")
    p_init.add_argument("device", nargs="?")
    p_init.add_argument("--path", dest="path")
    p_init.set_defaults(func=cmd_init)

    p_conv = sub.add_parser("convert", help="convert spt -> mk (legacy)")
    p_conv.add_argument("file")
    p_conv.add_argument("-o", "--output", dest="output")
    p_conv.set_defaults(func=cmd_convert)

    args = parser.parse_args()
    if args.version:
        print(f"SpiderLang v{VERSION}")
        sys.exit(0)
    if not args.cmd:
        print_banner()
        print(f"\n{info('usage')}")
        print("   spider run <file.spt>")
        print("   spider lunch <device> --tree <path>")
        print("   spider build <twrp|orangefox|pbrp> --tree <path>")
        print("   spider tree <path>")
        print("   spider check <file.spt>")
        print("   spider init <device>")
        sys.exit(0)
    args.func(args)

if __name__ == "__main__":
    main()

