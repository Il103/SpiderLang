# Spider CLI — Native .spt Build

```
spider run <file.spt>              Run any SpiderLang file
spider lunch <device> --tree <path> Select device (like Android lunch)
spider build <target> --tree <path> Build recovery natively
spider check <file.spt>            Check syntax only
spider init <device> --path <path> Init new device tree
spider convert <file.spt> --to mk  Legacy compat (not used)
```

## Full Flow (like AOSP)

Old (mk):
```
source build/envsetup.sh
lunch omni_X6886-eng
mka recoveryimage
```

Spider (native .spt):
```
spider lunch X6886 --tree device/infinix/X6886
spider build twrp --tree device/infinix/X6886
# or
spider build orangefox --tree device/xiaomi/sweet
```

## Build Targets

- `twrp` / `twrp` — TeamWin Recovery Project
- `orangefox` / `ofox` — OrangeFox Recovery
- `pbrp` — PitchBlack Recovery
- `shrp` — Sky Hawk Recovery

All targets use the same `BoardConfig.spt` — just change `recovery.type`.
