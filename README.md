# SpiderLang — The 1601st Programming Language
### Created by Beru

> Write in SpiderLang, run everything else.

SpiderLang is a modern, general-purpose language built from scratch by one developer — Beru.

It was created to be the 1601st language in the world — a language that doesn't compete with other 1600 languages, but connects to all of them.

## Vision

All 1600+ languages exist. SpiderLang is the next one — the universal bridge. Instead of replacing C, C++, Python, JavaScript, Rust, and others, SpiderLang can call them all natively through a unified FFI.

## Why SpiderLang?

- **General Purpose** — file system, networking, math, collections, everything built-in
- **Familiar Syntax** — clean blend of Python + Kotlin + Rust + JavaScript
- **Universal FFI** — `use python "ai.py"` , `use cpp "math.cpp"` — one syntax to call any language
- **Plugin Architecture** — support for 1600+ languages via `src/spider/ffi/<lang>.py` — add a new language in 20 lines
- **Size System** — `64.MB == 65536.KB == 67108864.B` — unified units from B to EB (binary 1024)
- **Android Recovery DSL** — replaces `BoardConfig.mk` with `BoardConfig.spt`
- **Safe & Strict** — line:col error reporting, no silent bugs
- **Solo Built** — designed, specified, and implemented by one person: Beru. Lexer, Parser, AST, VM all handwritten from scratch.

## Extension

`.spt` (primary) and `.spider`

## Quick Start

```bash
pip install -e .
spider run examples/hello.spt
spider run examples/BoardConfig.spt
spider build twrp --tree device/infinix/X6886
spider convert BoardConfig.spt --to mk
spider check BoardConfig.spt
```

## Example

```spider
let name = "Beru"
print("Hello {name} 🔥")

func factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
print(factorial(5))  // 120

let nums = [1, 2, 3, 4]
let doubled = nums.map(x => x * 2)
print(doubled) // [2, 4, 6, 8]

// Universal FFI — call any language
use python "ai.py" as ai
use cpp "math.cpp" as math
print(ai.predict([1,2,3]))
print(math.add(10, 20))
```

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
spider build twrp --tree device/infinix/X6886
# Generates out/BoardConfig.mk and builds recovery.img
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
spider run <file.spt>              Run a SpiderLang file
spider build twrp --tree <path>    Build TWRP recovery from device tree
spider convert <file.spt> --to mk  Convert .spt to .mk
spider check <file.spt>            Check syntax only
```

## Architecture

```
src/spider/
├── lexer.py      // Handmade, char-by-char, no regex libs
├── parser.py     // Recursive-descent, handmade
├── ast_nodes.py  // All nodes
├── interpreter.py // Tree-walk VM + SpiderSize + board DSL
├── ffi/          // Universal FFI plugins
│   ├── registry.py
│   ├── python.py
│   ├── cpp.py
│   └── js.py     // add new lang in 20 lines
└── cli.py        // spider binary with ASCII art
```

From scratch: No `eval`, no `exec`, no ANTLR, no PLY — every token and node is built by hand.

## License

MIT — by Beru
