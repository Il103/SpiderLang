# SpiderLang — one language, every Android device
### Created by Beru

> Write in SpiderLang, run everything else.

SpiderLang is a modern, general-purpose language built from scratch by one
developer — Beru. It is not one more language competing with the others: it is
_the_ language that understands and drives the entire Android device-tree
ecosystem natively — every device, every SoC, every recovery.

## Vision

Instead of replacing C, C++, Python, JavaScript, Rust, or the hundreds of `.mk`,
`.fstab` and `.sh` files scattered across Android device trees, SpiderLang reads
them all **as itself**. A device tree is not a pile of scripts to you — it is
one structure the language simply understands. The build pipeline is native:
`.spt -> lexer -> parser -> AST -> IR`, no `.mk` needed. And through a unified
FFI, SpiderLang can call any other language when you genuinely need it.

## Why SpiderLang?

- **The language understands any device tree** — codename, recovery variant,
  partitions, A/B slots and lunch combos are derived *by the language itself*
  from whatever is actually in the tree. No per-device scripts.
- **Reads every file in a tree natively** — `BoardConfig.spt`, `ofox_*.st`,
  `omni_*.st`, `pbrp_*.st`, `shrp_*.st`, `device.mk`, `fstab.*`, `vendorsetup.sh`.
  If there is a `.spt`, that is the tree.
- **Every recovery supported** — TWRP, OrangeFox, PitchBlack (PBRP), SkyHawk
  (SHRP), RedWolf, and more — each detected from its codename file (`.st`/`.mk`).
- **First-class file I/O** — `read()`, `readlines()`, `listdir()`, `write()`
  and `understand()` are built into the language core, not shipped as scripts.
- **Universal FFI** — `use python "ai.py"`, `use cpp "math.cpp"` — one syntax
  to call any language.
- **Size system** — `64.MB == 65536.KB == 67108864.B` — B to EB (binary 1024).
- **Android Recovery DSL** — `board { ... }` replaces `BoardConfig.mk`; the
  **second language `.st`** defines the images & flags (`image "recovery" { }`,
  `image "vendor_boot" { }`, `image "boot" { }`) for any codename recovery.
- **Safe & Strict** — line:col error reporting, no silent bugs.
- **Solo built** — designed, specified, and implemented by one person: Beru.
  Lexer, Parser, AST, VM all handwritten from scratch.

## Extension

`.spt` (primary), `.spider`, and the second language `.st` (recovery / image
definitions, replacing the old codename `.mk` files).

## Quick Start

```bash
pip install -e .
spider init falcon --path device/xiaomi/falcon   # scaffold a device tree
spider info device/xiaomi/falcon                  # the language understands it
spider tree device/xiaomi/falcon                  # tree + partitions + codename
spider build twrp --tree device/xiaomi/falcon     # build recovery.img
spider build vendor_boot --tree device/xiaomi/falcon   # build vendor_boot.img
spider build boot --tree device/xiaomi/falcon          # build boot.img
spider convert BoardConfig.spt --to mk
spider check BoardConfig.spt
```

## Example

```spider
let name = "Beru"
print("Hello {name}")

func factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
print(factorial(5))  // 120

// First-class file I/O — the language reads a device tree by itself
let tree = understand("device/xiaomi/falcon")
print("codename : {tree.codename}")
print("recovery : {tree.recoveries}")
print("partitions: {tree.partitions}")

// Universal FFI — call any language
use python "ai.py" as ai
use cpp "math.cpp" as math
```

## Second Language (.st) — recovery & image definitions

The `.st` files replace the old codename `.mk` files. The `image` block drives
any of the three image types, each with its own header & flags:

```spider
// ofox_falcon.st — OrangeFox over an A/B device
image "vendor_boot" {
    kernel: "Image.gz-dtb",
    vendor_boot_ramdisk: ["vendor-ramdisk", "ofox-ramdisk"],
    vendor_dtb: "kona.dtb",
    header_v3_v4: true,
    flags: ["OF_USE_TWRP_SAR_DETECT", "OF_USE_MAGISKBOOT"]
}
```

The language knows every image type & flag natively — `recovery.img`
(header v0-2), `vendor_boot.img` (header v3/v4), and `boot.img` — so any
`fstab.*` and any `*_<codename>.st` is read automatically.

## Android Recovery Example

```spider
// BoardConfig.spt
board {
    arch: "arm64",
    arch_variant: "armv8-a",
    bootloader: {
        kernel_pagesize: 4096,
        boot_partition_size: 64.MB
    },
    recovery: {
        type: "twrp",
        include_crypto: true,
        flags: ["TW_EXCLUDE_APEX", "TW_HAS_MTP"]
    }
}

use cpp "validators/partition_check.cpp" as checker
checker.verify_sizes(board.bootloader)
```

Build it:

```bash
spider build twrp --tree device/xiaomi/falcon
# Generates out/board.json and builds recovery.img
spider build vendor_boot --tree device/xiaomi/falcon
# Stages vendor ramdisk fragments, packs vendor_boot.img (header v3/v4)
spider build boot --tree device/xiaomi/falcon
# Packs boot.img (header v0-4)
```

## Size Units

All binary (1024):

| Unit | Bytes |
|------|-------|
| B    | 1 |
| KB / KIB | 1024 |
| MB / MIB | 1048576 |
| GB / GIB | 1073741824 |
| TB / TIB | 1099511627776 |
| PB / PIB | 1125899906842624 |
| EB / EIB | 1152921504606846976 |

```spider
64.MB == 65536.KB == 67108864.B  // true
1.GB == 1024.MB                  // true
```

## CLI

```
spider info <path>               Full device report (language understanding)
spider tree <path>               Device tree + partitions + A/B + codename
spider lunch <device>            Select device (auto-detects codename+variant)
spider build <target> --tree .. Build any recovery OR image type
spider build recovery --tree .. Build recovery.img  (header v0-2)
spider build vendor_boot --tree ..  Build vendor_boot.img (header v3/v4)
spider build boot --tree ..     Build boot.img (header v0-4)
spider build twrp --tree <path> Build TWRP recovery natively from .spt
spider run <file.spt>           Run a SpiderLang file (.spt / .st)
spider convert <file.spt> --to mk  Convert .spt to .mk (legacy)
spider check <file.spt>         Check syntax only
```

## Architecture

```
src/spider/
├── lexer.py      // Handmade, char-by-char, no regex libs
├── parser.py     // Recursive-descent, handmade
├── ast_nodes.py  // All nodes
├── interpreter.py // Tree-walk VM + SpiderSize + board DSL + file I/O
│                  //   + understand() — reads any device tree natively
├── recoveries.py // Language knowledge: every recovery + its codename/flags
├── images.py     // Language knowledge: recovery.img / vendor_boot.img / boot.img
│                  //   + every header version & flag set
├── themes.py     // Per-command CLI identities (logos + colours)
├── ffi/          // Universal FFI plugins
│   ├── registry.py
│   ├── python.py
│   ├── cpp.py
│   └── js.py
└── cli.py        // spider binary with handcrafted ASCII per command
```

From scratch: No `eval`, no `exec`, no ANTLR, no PLY — every token and node is
built by hand.

## License

MIT — by Beru
