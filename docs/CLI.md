# Spider CLI — Native Build & Diagnostics

```
spider run <file.spt|.st>         Run any SpiderLang file
spider lunch <device> [--tree]    Select device (auto-detects codename+variant)
spider check <tree>               FULL recovery diagnostic (score + verdict)
spider check <file.spt|.st>       Syntax + .st-dialect check
spider build <target> --tree <p>  Build recovery / vendor_boot / boot .img
spider init <device> [--path]     Scaffold a new device tree
spider tree <path>                Device tree + partitions + A/B + codename
spider info <path>                Full device report
spider show <file>                Highlighted source
spider convert <file.spt> --to mk Legacy compat (not used)
```

## If you don't give a tree path

`lunch`, `build`, `info` and the full `check` all auto-discover the device tree
(`_default_tree`) — so `spider check` on a directory just works, and `init`
derives a sensible `device/<brand>/<device>` location when `--path` is omitted.

## Full Flow (like AOSP)

Old (mk):
```
source build/envsetup.sh
lunch omni_X6886-eng
mka recoveryimage
```

Spider (native .spt/.st):
```
spider init sweet --path device/xiaomi/sweet
spider check device/xiaomi/sweet        # is it complete? score/verdict
spider build twrp   --tree device/xiaomi/sweet
spider build vendor_boot --tree device/xiaomi/sweet
```

## Build Targets

- `twrp` / `omni` — TeamWin Recovery Project
- `orangefox` / `ofox` — OrangeFox Recovery
- `pbrp` / `pitchblack` — PitchBlack Recovery
- `shrp` — Sky Hawk Recovery
- `redwolf` / `rw` — RedWolf Recovery

## Image types

- `recovery.img` (header v0-2) — default for a recovery build
- `vendor_boot.img` (header v3/v4) — A/B, kernel + vendor ramdisk
- `boot.img` (header v0-4) — kernel + boot ramdisk

## Hidden capabilities (not CLI flags)

- `magiskboot()` — inspect/verify boot + recovery image headers (magic,
  page size, kernel/ramdisk sizes, OS version, truncated?)
- `soong()` — read and validate Android.bp build rules natively

These are first-class language builtins, used quietly by `spider check` and
`spider build` — you never call them explicitly.
