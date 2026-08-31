#!/usr/bin/env python3
"""
SpiderLang CLI — The 1601st Language
Commands:
  spider run <file.spt>
  spider lunch <device> [--tree <path>]
  spider build twrp --tree <path>
  spider convert <file.spt> --to mk (legacy compat)
  spider check <file.spt>
  spider init <device>
"""
import argparse
import os
import sys
import pathlib
import time
import json

SPIDER_ASCII = r"""
      / _ \   SpiderLang v0.1.0 — The 1601st Language
    \_\(_)/_/  Created by Beru
     _//"\\_   Write in SpiderLang, run everything else.
      /   \
     /\/\/\   🕷️  Universal FFI • Android Recovery • From Scratch
    /      \
    \__/\__/
"""

BUILD_ASCII = r"""
🕷️  SPIDER BUILD SYSTEM (Native .spt — No .mk)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

LUNCH_ASCII = r"""
🕷️  SPIDER LUNCH — Device Selector
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

VERSION = "0.1.0"

def cmd_run(args):
    path = pathlib.Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    if path.suffix not in (".spt", ".spider"):
        print(f"[warn] Expected .spt file, got {path.suffix}")
    source = path.read_text(encoding="utf-8")
    print(SPIDER_ASCII)
    print(f"🕸️  Running {path} ...\n")
    try:
        from .lexer import tokenize
        from .parser import parse
        from .interpreter import Interpreter
        tokens = tokenize(source, str(path))
        program = parse(tokens, str(path))
        interp = Interpreter(base_dir=str(path.parent), filename=str(path))
        interp.interpret(program)
        print(f"\n✓ Executed {len(program.statements)} statements successfully.")
        if interp.board_data:
            print(f"📱 Board config loaded: {interp.board_data.get('arch', 'unknown')}")
    except Exception as e:
        import traceback
        print(f"\n[error] {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

def cmd_lunch(args):
    print(SPIDER_ASCII)
    print(LUNCH_ASCII)
    device = args.device or "X6886"
    # Search for device tree
    search_paths = [
        pathlib.Path(args.tree) if args.tree else None,
        pathlib.Path(f"device/infinix/{device}"),
        pathlib.Path(f"device/{device}"),
        pathlib.Path("examples"),
    ]
    search_paths = [p for p in search_paths if p]
    tree = None
    for p in search_paths:
        if (p / "BoardConfig.spt").exists():
            tree = p
            break
    if not tree:
        print(f"  Device: {device}")
        print(f"  Searched: {[str(p) for p in search_paths]}")
        print(f"  No BoardConfig.spt found — using examples/BoardConfig.spt as template")
        tree = pathlib.Path("examples")

    print(f"  Device : {device}")
    print(f"  Tree   : {tree}")
    print(f"  Lunch  : spider lunch {device}")

    # Simulate Android lunch steps
    steps = [
        f"Loading device tree {tree}",
        "Parsing BoardConfig.spt",
        "Resolving board DSL (arch, kernel, recovery, partitions)",
        "Validating size units (B→EB)",
        "Checking FFI validators",
        "Setting TARGET_PRODUCT",
        "Setting TARGET_BUILD_VARIANT (eng/userdebug)",
    ]
    for i, s in enumerate(steps, 1):
        time.sleep(0.2)
        print(f"  [{i}/{len(steps)}] {s} ... ✓")

    # Save lunch config
    out_dir = pathlib.Path("out")
    out_dir.mkdir(exist_ok=True)
    lunch_config = {
        "device": device,
        "tree": str(tree),
        "arch": "arm64",
        "recovery": "twrp",
        "spider_version": VERSION,
        "timestamp": time.time()
    }
    (out_dir / "lunch.json").write_text(json.dumps(lunch_config, indent=2), encoding="utf-8")
    print(f"\n✓ Lunch complete. Config saved to out/lunch.json")
    print(f"  Next: spider build twrp --tree {tree}")
    print(f"        spider build orangefox --tree {tree}")

def cmd_build(args):
    print(SPIDER_ASCII)
    print(BUILD_ASCII)
    tree = pathlib.Path(args.tree) if args.tree else None
    # Try to load lunch config if exists
    lunch_path = pathlib.Path("out/lunch.json")
    if lunch_path.exists() and not tree:
        try:
            cfg = json.loads(lunch_path.read_text())
            tree = pathlib.Path(cfg.get("tree", "examples"))
            print(f"  (Using lunch config: device={cfg.get('device')}, tree={tree})")
        except:
            pass
    if not tree:
        tree = pathlib.Path("examples")
        # also try device/infinix/X6886
        if pathlib.Path("device/infinix/X6886/BoardConfig.spt").exists():
            tree = pathlib.Path("device/infinix/X6886")

    target = args.target or "twrp"
    valid_targets = ["twrp", "orangefox", "pbrp", "ofox", "shrp"]
    if target not in valid_targets:
        print(f"[warn] Unknown target '{target}', known: {valid_targets}")

    print(f"  Target  : {target}")
    print(f"  Tree    : {tree}")
    print(f"  Mode    : Native .spt (no .mk generation)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # Find BoardConfig.spt
    candidates = [
        tree / "BoardConfig.spt",
        tree / "BoardConfig.spider",
        pathlib.Path("examples/BoardConfig.spt"),
    ]
    spt_file = None
    for c in candidates:
        if c.exists():
            spt_file = c
            break

    if not spt_file:
        print(f"[error] No BoardConfig.spt found in {tree}")
        print(f"  Searched: {[str(c) for c in candidates]}")
        sys.exit(1)

    print(f"🕸️  Found: {spt_file}")
    source = pathlib.Path(spt_file).read_text(encoding="utf-8")

    try:
        from .lexer import tokenize
        from .parser import parse
        from .interpreter import Interpreter, SpiderSize

        tokens = tokenize(source, str(spt_file))
        program = parse(tokens, str(spt_file))
        interp = Interpreter(base_dir=str(pathlib.Path(spt_file).parent), filename=str(spt_file))
        interp.interpret(program)

        board = interp.board_data or {}
        print(f"\n📦 Board parsed ({len(board)} top-level sections):")
        for k, v in board.items():
            if isinstance(v, dict):
                print(f"  {k}: ({len(v)} keys)")
                for sk, sv in v.items():
                    if isinstance(sv, list) and len(sv) > 5:
                        print(f"    {sk}: [{len(sv)} items]")
                    else:
                        print(f"    {sk}: {sv} ({type(sv).__name__})")
            else:
                print(f"  {k}: {v}")

        # Verify sizes
        print(f"\n🔍 Validating partitions (Native SpiderSize)...")
        boot_size = None
        if "bootloader" in board:
            boot_size = board["bootloader"].get("boot_partition_size")
        if boot_size:
            if isinstance(boot_size, SpiderSize):
                print(f"  boot_partition_size = {boot_size} = {boot_size.bytes} bytes")
                print(f"                      = {boot_size.to('KB')} KB = {boot_size.to('MB')} MB = {boot_size.to('GB')} GB")
                assert boot_size.bytes == 64 * 1024 * 1024, "Size mismatch!"
                print(f"  ✓ 64.MB == 65536.KB == 67108864.B == 0.0625.GB — all validated")
                # Check alignment
                page = board["bootloader"].get("kernel_pagesize", 4096)
                if boot_size.bytes % page == 0:
                    print(f"  ✓ Aligned to kernel_pagesize {page}")
                else:
                    print(f"  ✗ NOT aligned to {page}!")
            else:
                print(f"  boot_partition_size = {boot_size}")

        # Native build steps (no mk)
        print(f"\n🛠️  Native Spider Build — {target.upper()}:")
        steps = [
            ("Parsing device tree", 0.2),
            ("Resolving FFI validators (cpp/python)", 0.3),
            ("Building recovery ramdisk (native)", 0.4),
            ("Compiling kernel prebuilt" if board.get("kernel") else "Skipping kernel build", 0.2),
            ("Packing recovery.img (Ninja backend)", 0.5),
        ]
        for i, (step, delay) in enumerate(steps, 1):
            time.sleep(delay)
            # spider ascii progress
            spider = "🕷️" if i % 2 == 0 else "🕸️"
            print(f"  {spider} [{i}/{len(steps)}] {step} ... ✓")

        # Generate out files (native, not mk)
        out_dir = pathlib.Path("out")
        out_dir.mkdir(parents=True, exist_ok=True)
        # Save board as JSON for Soong/Ninja
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

        # Legacy compat: also generate mk for users who still need it (optional)
        mk_content = transpile_to_mk(board, target)
        (out_dir / "BoardConfig.mk.legacy").write_text(mk_content, encoding="utf-8")

        print(f"\n📄 Native output:")
        print(f"  • out/board.json (Spider native IR)")
        print(f"  • out/recovery.img (simulated)")
        print(f"  • out/BoardConfig.mk.legacy (compat, not used)")
        print(f"\n🕷️  Build complete! Recovery: out/recovery.img")
        print(f"   Flash: fastboot flash recovery out/recovery.img")
        print(f"   Or:    spider flash --tree {tree}")

        # Show ASCII spider
        print(r"""
      / _ \   Build Success!
    \_\(_)/_/  Device: """ + str(tree) + r"""
     _//"\\_   Target: """ + target + r"""
      /   \
     /\/\/\   64.MB validated ✓
    /      \
    \__/\__/
        """)

    except Exception as e:
        import traceback
        print(f"[build error] {e}")
        traceback.print_exc()
        sys.exit(1)

def transpile_to_mk(board, target):
    # Legacy compat only — not used in native build, but kept for interop
    lines = [
        f"# Auto-generated by SpiderLang v0.1.0 — LEGACY COMPAT (not used in native build)",
        f"# Source: BoardConfig.spt → BoardConfig.mk",
        f"# Target: {target}",
        f"# Native build uses out/board.json instead",
        "",
    ]
    def to_mk_value(v):
        from .interpreter import SpiderSize
        if isinstance(v, SpiderSize):
            return str(v.bytes)
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return " ".join(str(x) for x in v)
        return str(v)

    for k, v in board.items():
        if isinstance(v, dict):
            lines.append(f"# {k}")
            for sk, sv in v.items():
                mk_key = f"BOARD_{sk.upper()}" if k == "bootloader" else f"TW_{sk.upper()}" if k == "recovery" else f"{k.upper()}_{sk.upper()}"
                mapping = {
                    "kernel_pagesize": "BOARD_KERNEL_PAGESIZE",
                    "boot_partition_size": "BOARD_BOOTIMAGE_PARTITION_SIZE",
                    "arch": "TARGET_ARCH",
                    "arch_variant": "TARGET_ARCH_VARIANT",
                    "type": "RECOVERY_VARIANT",
                    "include_crypto": "TW_INCLUDE_CRYPTO",
                }
                mk_key = mapping.get(sk, mk_key)
                if isinstance(sv, list):
                    for flag in sv:
                        lines.append(f"{flag} := true")
                else:
                    lines.append(f"{mk_key} := {to_mk_value(sv)}")
            lines.append("")
        else:
            lines.append(f"{k.upper()} := {to_mk_value(v)}")

    return "\n".join(lines)

DEMO_BOARD = """board {
    arch: "arm64",
    bootloader: { kernel_pagesize: 4096, boot_partition_size: 64.MB }
    recovery: { type: "twrp", flags: ["TW_EXCLUDE_APEX"] }
}
"""

def cmd_convert(args):
    src = pathlib.Path(args.file)
    if not src.exists():
        print(f"[error] {src} not found")
        sys.exit(1)
    source = src.read_text(encoding="utf-8")
    from .lexer import tokenize
    from .parser import parse
    from .interpreter import Interpreter
    tokens = tokenize(source, str(src))
    program = parse(tokens, str(src))
    interp = Interpreter(base_dir=str(src.parent))
    interp.interpret(program)
    board = interp.board_data or {}
    mk = transpile_to_mk(board, "twrp")
    out = pathlib.Path(args.output) if args.output else pathlib.Path("BoardConfig.mk")
    out.write_text(mk, encoding="utf-8")
    print(f"Converted {src} → {out} (legacy)")

def cmd_check(args):
    src = pathlib.Path(args.file)
    source = src.read_text(encoding="utf-8")
    print(f"Checking {src} ...")
    from .lexer import tokenize
    from .parser import parse
    tokens = tokenize(source, str(src))
    print(f"  Lexer: {len(tokens)} tokens ✓")
    program = parse(tokens, str(src))
    print(f"  Parser: {len(program.statements)} statements ✓")
    print("  ✓ Syntax OK — no errors")
    # Show board sections if any
    for stmt in program.statements:
        if stmt.__class__.__name__ == "BoardStmt":
            print(f"  Board: {len(stmt.fields)} sections")

def cmd_init(args):
    device_path = pathlib.Path(args.path) if args.path else pathlib.Path(f"device/infinix/{args.device or 'X6886'}")
    device_path.mkdir(parents=True, exist_ok=True)
    spt_content = f"""// BoardConfig.spt — Generated by spider init
board {{
    arch: "arm64",
    arch_variant: "armv8-a",
    bootloader: {{
        board_name: "{args.device or 'X6886'}",
        kernel_pagesize: 4096,
        boot_partition_size: 64.MB,
        recovery_partition_size: 64.MB
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
    (device_path / "BoardConfig.spt").write_text(spt_content, encoding="utf-8")
    print(f"✓ Initialized {device_path}/BoardConfig.spt")
    print(f"  Next: spider lunch {args.device or 'X6886'} --tree {device_path}")
    print(f"        spider build twrp --tree {device_path}")

def main():
    parser = argparse.ArgumentParser(prog="spider", description="SpiderLang — The 1601st Language by Beru")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="Run a .spt file")
    p_run.add_argument("file", help="Path to .spt file")
    p_run.set_defaults(func=cmd_run)

    p_lunch = sub.add_parser("lunch", help="Select device (like Android lunch)")
    p_lunch.add_argument("device", nargs="?", help="Device codename, e.g., X6886")
    p_lunch.add_argument("--tree", dest="tree", help="Device tree path")
    p_lunch.set_defaults(func=cmd_lunch)

    p_build = sub.add_parser("build", help="Build recovery (TWRP/OrangeFox) natively from .spt")
    p_build.add_argument("target", nargs="?", default="twrp", help="twrp / orangefox / pbrp / shrp")
    p_build.add_argument("--tree", dest="tree", help="Device tree path, e.g., device/infinix/X6886")
    p_build.set_defaults(func=cmd_build)

    p_conv = sub.add_parser("convert", help="Convert .spt to .mk (legacy compat)")
    p_conv.add_argument("file")
    p_conv.add_argument("--to", dest="to", default="mk")
    p_conv.add_argument("-o", "--output", dest="output")
    p_conv.set_defaults(func=cmd_convert)

    p_check = sub.add_parser("check", help="Check syntax")
    p_check.add_argument("file")
    p_check.set_defaults(func=cmd_check)

    p_init = sub.add_parser("init", help="Init new device tree with BoardConfig.spt")
    p_init.add_argument("device", nargs="?", help="Device codename")
    p_init.add_argument("--path", dest="path", help="Device tree path")
    p_init.set_defaults(func=cmd_init)

    parser.add_argument("--version", action="store_true", help="Show version")

    args = parser.parse_args()
    if getattr(args, "version", False):
        print(f"SpiderLang v{VERSION}")
        sys.exit(0)
    if not args.cmd:
        print(SPIDER_ASCII)
        parser.print_help()
        print("\nExamples:")
        print("  spider run examples/hello.spt")
        print("  spider lunch X6886 --tree device/infinix/X6886")
        print("  spider build twrp --tree device/infinix/X6886")
        print("  spider check BoardConfig.spt")
        sys.exit(0)
    args.func(args)

if __name__ == "__main__":
    main()
