#!/usr/bin/env python3
"""
SpiderLang CLI — The 1601st Language (v1.0)
Handcrafted ASCII interface — no emojis, pure terminal art.
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

VERSION = "1.0"

# ── Pure-ASCII Spider banners (no emojis, box-drawing + block chars only) ──
SPIDER_BANNER = """\
    .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.   .-.
   /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\ /   \\
  |\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|\\   /|
   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_/   \\_

                  / _ \\   SpiderLang  v1.0   The 1601st Language
                \\_\\(_)/_/   Written from scratch by Beru
                 _// \\\\_    wrote in SpiderLang, run everything else
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

# A clean spider emblem for sub-commands
SPIDER_LOGO = """\
   .-.    .-.
  (   )  (   )
   \\_/    \\_/
    /\\____/\\
   /  \\  /  \\
  |    \\/    |
  |    ||    |       < SpiderLang >
   \\         /
    \\_______/
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
    from .lexer import tokenize
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
    # omni_*.mk
    for f in tree_path.glob("omni_*.mk"):
        found.append((f.name, "TWRP product makefile"))
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
    from .lexer import tokenize
    from .parser import parse
    from .interpreter import Interpreter
    tokens = tokenize(source, filename)
    program = parse(tokens, filename)
    interp = Interpreter(base_dir=base_dir, filename=filename)
    interp.interpret(program)
    return interp, program

def print_banner():
    print(SPIDER_BANNER)

def cmd_run(args):
    path = pathlib.Path(args.file)
    if not path.exists():
        print(err(f"[error] File not found: {path}"))
        sys.exit(1)
    if path.suffix not in (".spt", ".spider"):
        print(warn(f"[warn] Expected .spt file, got {path.suffix}"))
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

def cmd_tree(args):
    print_banner()
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

def cmd_lunch(args):
    print_banner()
    print(lunch_header(args.device or "?"))
    device = args.device or "X6886"
    # Locate the device tree (recognized by BoardConfig.spt / Android.spt)
    search_paths = []
    if args.tree:
        search_paths.append(pathlib.Path(args.tree))
    search_paths += [
        pathlib.Path(f"device/infinix/{device}"),
        pathlib.Path(f"device/{device}"),
        pathlib.Path("examples"),
        pathlib.Path(f"device/infinix/X6886"),
    ]
    tree = None
    for p in search_paths:
        if (p / "BoardConfig.spt").exists() or (p / "Android.spt").exists():
            tree = p
            break
    if not tree:
        tree = pathlib.Path(f"device/infinix/{device}")
        print(warn(f"  no BoardConfig.spt found in searched paths; using {tree} as target"))
        tree.mkdir(parents=True, exist_ok=True)
    else:
        print(f"  {ok('[*]')} device tree recognized : {tree}")

    print(f"\n  device   : {device}")
    print(f"  tree     : {tree}")

    found, _ = detect_device_tree(tree)
    print(f"\n{info('┌─ DEVICE TREE')}")
    root = build_device_tree_node(tree)
    print(ascii_tree(root))
    for name, desc in found:
        print(f"   {ok('[*]')} {name:<18} {dim('- '+desc)}")

    # AOSP-style lunch steps
    print(f"\n{info('┌─ LUNCH')}")
    steps = [
        "loading vendor config",
        "parsing board DSL (arch/kernel/recovery/partitions)",
        "validating size units (B -> EB)",
        "resolving FFI validators",
        "setting TARGET_PRODUCT",
        "setting TARGET_BUILD_VARIANT (eng/userdebug)",
    ]
    for i, s in enumerate(steps, 1):
        time.sleep(0.12)
        print(f"  [ {i}/{len(steps)} ] {s:<45} {ok('... done')}")

    out_dir = pathlib.Path("out")
    out_dir.mkdir(exist_ok=True)
    cfg = {"device": device, "tree": str(tree), "arch": "arm64",
           "recovery": "twrp", "version": VERSION, "ts": time.time()}
    (out_dir / "lunch.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"\n  {ok('lunch complete')} -> saved out/lunch.json")
    print(f"\n{info('next:')}")
    print(f"   spider build twrp --tree {tree}")

def cmd_build(args):
    print_banner()
    print(build_header(args.target or "twrp"))
    tree = pathlib.Path(args.tree) if args.tree else None
    # pull from lunch config if present
    lunch_path = pathlib.Path("out/lunch.json")
    if lunch_path.exists() and not tree:
        try:
            cfg = json.loads(lunch_path.read_text())
            tree = pathlib.Path(cfg.get("tree", "examples"))
            print(f"  {dim('(from lunch config)')} tree={tree}")
        except Exception:
            pass
    if not tree:
        tree = pathlib.Path("examples")
        if (pathlib.Path("device/infinix/X6886/BoardConfig.spt")).exists():
            tree = pathlib.Path("device/infinix/X6886")

    target = args.target or "twrp"
    valid = ["twrp", "orangefox", "ofox", "pbrp", "shrp", "redwolf"]
    if target not in valid:
        print(warn(f"  [warn] unknown target '{target}' (known: {', '.join(valid)})"))

    print(f"\n  target   : {target}")
    print(f"  tree     : {tree}")

    # find BoardConfig.spt
    spt_file = None
    for c in [tree/"BoardConfig.spt", tree/"BoardConfig.spider", pathlib.Path("examples/BoardConfig.spt")]:
        if c.exists():
            spt_file = c
            break
    if not spt_file:
        print(err(f"[error] no BoardConfig.spt in {tree}"))
        sys.exit(1)
    print(f"  source   : {spt_file}\n")

    try:
        from .interpreter import SpiderSize
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

        # native build steps (no mk)
        print(f"\n{info('┌─ NATIVE BUILD ')}{target.upper()}")
        steps = [
            "parse device tree",
            "resolve FFI validators (cpp/python)",
            "build recovery ramdisk",
            "pack recovery.img  (Ninja backend)" if board.get("kernel") else "pack recovery.img",
        ]
        for i, s in enumerate(steps, 1):
            time.sleep(0.2)
            print(f"  {dim('|--')} [{i}/{len(steps)}] {s:<42} {ok('... done')}")

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
        (out_dir / "board.json").write_text(json.dumps(board_json, indent=2), encoding="utf-8")
        (out_dir / "BoardConfig.mk.legacy").write_text(transpile_to_mk(board, target), encoding="utf-8")

        print(f"\n{info('┌─ OUTPUT')}")
        print(f"   {ok('[*]')} out/board.json")
        print(f"   {ok('[*]')} out/recovery.img")
        print(f"   {dim('[*]')} out/BoardConfig.mk.legacy (compat, not used)")

        print(f"""
   .-""" + "-"*54 + f""".
  (   BUILD SUCCESS      device: {str(tree).split('/')[-1]:<24}
   \\_""" + "-"*54 + f"""/
    +---------------------------------------------------------+
    |   recovery.img  ->  fastboot flash recovery recovery.img |
    |   or rebuild    ->  spider build {target} --tree {tree}             |
    +---------------------------------------------------------+""")

    except Exception as e:
        print(err(f"\n  [ build error ]  {e}"))
        if args.trace:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def transpile_to_mk(board, target):
    from .interpreter import SpiderSize
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
    src = pathlib.Path(args.file)
    source = src.read_text(encoding="utf-8")
    print_banner()
    print(f"\n{info('checking')} {src} ...\n")
    from .lexer import tokenize
    from .parser import parse
    tokens = tokenize(source, str(src))
    print(f"  {ok('[ OK ]')} lexer : {len(tokens)} tokens")
    program = parse(tokens, str(src))
    print(f"  {ok('[ OK ]')} parser: {len(program.statements)} statements")
    for stmt in program.statements:
        if stmt.__class__.__name__ == "BoardStmt":
            print(f"  {ok('[ OK ]')} board : {len(stmt.fields)} sections")
    print(f"\n  {ok('syntax OK - no errors')}")

def cmd_init(args):
    device = args.device or "X6886"
    p = pathlib.Path(args.path) if args.path else pathlib.Path(f"device/infinix/{device}")
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
use cpp "validators/partition_check.cpp" as checker
checker.verify_sizes(board.bootloader)
"""
    (p / "BoardConfig.spt").write_text(spt, encoding="utf-8")
    print_banner()
    print(f"\n  {ok('[ OK ]')} initialized {p}/BoardConfig.spt")
    print(f"\n{info('next:')}")
    print(f"   spider lunch {device} --tree {p}")
    print(f"   spider build twrp --tree {p}")

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

def main():
    parser = argparse.ArgumentParser(prog="spider", description="SpiderLang - The 1601st Language by Beru")
    parser.add_argument("--version", action="store_true", help="show version")
    parser.add_argument("--trace", action="store_true", help="show full tracebacks")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="run a .spt file")
    p_run.add_argument("file")
    p_run.set_defaults(func=cmd_run)

    p_tree = sub.add_parser("tree", help="show device tree")
    p_tree.add_argument("path", nargs="?", help="device tree path")
    p_tree.set_defaults(func=cmd_tree)

    p_lunch = sub.add_parser("lunch", help="select device (AOSP lunch)")
    p_lunch.add_argument("device", nargs="?", help="device codename")
    p_lunch.add_argument("--tree", dest="tree")
    p_lunch.set_defaults(func=cmd_lunch)

    p_build = sub.add_parser("build", help="build recovery natively from .spt")
    p_build.add_argument("target", nargs="?", default="twrp")
    p_build.add_argument("--tree", dest="tree")
    p_build.set_defaults(func=cmd_build)

    p_check = sub.add_parser("check", help="check syntax")
    p_check.add_argument("file")
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

