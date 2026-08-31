# `spider check` — the full recovery diagnostic

Unlike a plain syntax check, `spider check <tree>` understands the *whole*
recovery and tells you whether it's complete, what's missing, and whether it
will actually work. It returns a **score (0-100)** and a **verdict**.

## What it checks

1. **Tree understood** — codename, recovery variant, partitions detected by the
   language itself (no scripts).
2. **`.st` dialect purity** — the second-language files must not leak old
   makefile-isms (`LOCAL_`, `ifeq`, `PRODUCT_`, ...).
3. **Image completeness** — via the hidden `magiskboot()` engine: is
   `recovery.img` a real Android image (ANDROID! magic)? correct header version?
   kernel/ramdisk present? truncated?
4. **Important flags** — per-family essentials (e.g. `TW_HAS_MTP`,
   `TW_INCLUDE_CRYPTO`, `OF_USE_TWRP_SAR_DETECT`, `OF_USE_MAGISKBOOT`) are
   detected from the `.st`/`.mk`/`.spt` content.
5. **Soong (.bp)** — every `Android.bp` module is validated against the known
   Soong module types.

## Verdicts

- **COMPLETE** — every check passed (score 100).
- **PARTIAL** — no hard failures, but something is missing or optional.
- **NOT READY** — a hard failure: image truncated, unreadable tree, etc.

## Example

```
spider check device/xiaomi/sweet

  [ OK ] tree read & understood (codename=sweet)
  [ OK ] recovery variant: orangefox
  [ OK ] fstab read: 9 partitions (9 A/B)
  [ OK ] .st dialect pure (1 file(s), no .mk leaks)
  [ OK ] recovery.img: complete (header v2, 13.0.0)
  [ OK ] OF_USE_TWRP_SAR_DETECT: present — SAR detection
  [ OK ] OF_USE_MAGISKBOOT: present — magiskboot
  [ OK ] Soong: 14 module(s) in 2 .bp file(s), no issues

  SUMMARY
     checks  : 12   (ok=12  warn=0  fail=0)
     score   : 100/100
     verdict : COMPLETE
```

Pass a `.spt` / `.st` **file** instead of a directory and it falls back to a
syntax + dialect check:

```
spider check ofox_sweet.st
```
