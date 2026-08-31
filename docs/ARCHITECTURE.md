# Architecture — the big project

SpiderLang is built as a two-layer project: a **native chip** that owns the
real work, and a **thin host** that only carries requests to it and back.

```
┌─────────────────────────────┐
│  the host (Python)          │   thin bridge only — no logic of its own
│  cli / check / engine       │   builds & calls the chip, formats output
└──────────────┬──────────────┘
               │  subprocess
               ▼
┌─────────────────────────────┐
│  the chip (C++17 native)    │   the BRAIN — self-contained, from scratch
│  Android.tm lexer/parser/   │   no external libs, builds with plain g++
│  validator  +  magiskboot   │   bundles the real magiskboot for 4 ABIs
└─────────────────────────────┘
```

## The chip (`native/`)

A single standalone binary (`native/build/spider`) that needs **no Python**.
It is the brain: it lexes, parses and validates `Android.tm` itself, and it
peeks boot/recovery image headers itself.

```
native/
├── Makefile, CMakeLists.txt
├── src/
│   ├── main.cpp            # chip CLI: tm / check / chip / info / version
│   ├── tm/                 # Android.tm — the Soong successor, parsed natively
│   │   ├── lexer.{h,cpp}
│   │   ├── ast.h
│   │   ├── parser.{h,cpp}
│   │   └── validate.{h,cpp}
│   ├── chip/               # the chip's own concern
│   │   ├── chip.{h,cpp}    #   locate/run bundled magiskboot, header peek
│   └── util/
│       └── fs.{h,cpp}      # filesystem + string helpers
└── chip/                   # bundled magiskboot binaries (4 ABIs)
    ├── x86_64/magiskboot
    ├── x86/magiskboot
    ├── arm64/magiskboot
    └── arm/magiskboot
```

`chip` subcommands (hidden from the public surface):

- `spider tm file.tm` — parse + validate an `Android.tm` build file.
- `spider check image.img` — verify a boot/recovery header (magic, header
  version, page size, OS, truncated?).
- `spider chip <args>` — run the bundled magiskboot (unpack/repack/patch).
- `spider info` — confirm which ABI magiskboot is bundled.

## The host (`src/spider/`)

The host locates and (if needed) builds the chip, then works on top of it.

- `chip.py` — the bridge: `chip_binary()`, `chip_tm()`, `chip_check_image()`.
- `tools/magisk.py` — the language-level `magiskboot()` builtin. Its real work
  is delegated to the chip; it only falls back to a portable parser if the chip
  is unavailable (so `spider check` survives offline).

## Languages, not `.py`

The project's *real* surface is the file formats and the native chip:
`.spt` (the device tree language), `.st` (the recovery/image dialect), and now
**`.tm`** (`Android.tm`) for build definitions. Python exists only to glue them
to the CLI. The chip — C++ — is where the parsing and building actually live.

## Security

Everything is yours under MIT (see `LICENSE`). The chip is self-contained; the
bundled magiskboot is invoked only with arguments the user already controls.
