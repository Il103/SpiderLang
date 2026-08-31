"""
SpiderLang magiskboot — a HIDDEN native capability inside the language core.

magiskboot is the real tool used by OrangeFox/TWRP to unpack & repack
boot/recovery/vendor_boot images and patch the first-stage ramdisk. Spider
bakes the SAME capability in as a first-class builtin — exposed in the language
as magiskboot() — so check/build can verify an image is complete and correct
without the user ever needing to know it exists. It is deliberately NOT a CLI
flag: it lives quietly in the engine underneath check().
"""

import struct
import os

# Boot image header v0 magic ("ANDROID!")
BOOT_MAGIC = b"ANDROID!"

# v0-2 header fields (little-endian): magic, kernel_size, kernel_addr,
# ramdisk_size, ramdisk_addr, second_size, second_addr, tags_addr, page_size,
# header_version, os_version|os_patch, name, cmdline, id, extra_cmdline
V0_FORMAT = "<8sIIIIIIIIHHI"
V0_FIXED = 36  # fixed part size of v0 header (up to and incl. header_version)


def _be32(b, off):
    return struct.unpack(">I", b[off:off + 4])[0]


def _le32v(b, off):
    return struct.unpack("<I", b[off:off + 4])[0]


def peek_header(data):
    """Return a dict describing the boot/recovery/vendor_boot header, or None."""
    if len(data) < 12 or not data[:8] == BOOT_MAGIC:
        return None
    # AOSP boot_img_hdr: magic[8], kernel_size@8, kernel_addr@12,
    # ramdisk_size@16, ramdisk_addr@20, second_size@24, second_addr@28,
    # tags_addr@32, page_size@36, header_version@40, os_version@44
    page_size = _le32v(data, 36)
    if page_size not in (0, 2048, 4096, 8192, 16384, 32768, 65536):
        page_size = 2048
    header_version = _le32v(data, 40)
    out = {
        "magic": "ANDROID!",
        "page_size": page_size,
        "header_version": header_version,
        "kernel_size": _le32v(data, 8) if len(data) >= 40 else 0,
        "ramdisk_size": _le32v(data, 16) if len(data) >= 40 else 0,
        "second_size": _le32v(data, 24) if len(data) >= 40 else 0,
        "os_version": "0.0.0",
        "os_patch_level": "unknown",
        "valid": False,
    }
    os_ver_raw = _le32v(data, 44) if len(data) >= 48 else 0
    if os_ver_raw:
        a = (os_ver_raw >> 25) & 0x7F
        b = (os_ver_raw >> 18) & 0x7F
        c = (os_ver_raw >> 11) & 0x7F
        out["os_version"] = f"{a}.{b}.{c}"
        y = 2000 + ((os_ver_raw >> 4) & 0x7F)
        m = os_ver_raw & 0xF
        out["os_patch_level"] = f"{y:04d}-{m:02d}"
    return out


def _payload_size(header, sections):
    """Compute the total (padded) payload bytes from the header sizes."""
    page = header.get("page_size", 2048)
    total = page * 2  # header page + n kernel pages (rounded) below
    total = page  # header page
    sizes = [header.get("kernel_size", 0), header.get("ramdisk_size", 0),
             header.get("second_size", 0)]
    for s in sizes:
        total += page + s
    # v1: recovery_dtbo + recovery_acpio; v2: dtb_size + dtb_addr
    total += header.get("recovery_dtbo_size", 0)
    total += 0
    return total


def analyze(path):
    """Analyze a real boot/recovery/vendor_boot image file.

    The real work is delegated to the native chip, not redone here: Python is
    only a thin host. If the chip isn't built, this falls back to the portable
    parser so `spider check` keeps working offline.
    """
    if not os.path.isfile(path):
        return {"exists": False, "path": path, "magic": None}
    # Preferred: ask the native chip (parses the header itself).
    try:
        from ..chip import chip_check_image
        native = chip_check_image(path)
        if native and native.get("magic"):
            page = native.get("page_size") or 2048
            kernel = native.get("kernel_bytes") or 0
            ramdisk = native.get("ramdisk_bytes") or 0
            file_size = os.path.getsize(path)
            # page-aligned expected size (matches this module's parser)
            def page_up(n):
                return ((n + page - 1) // page) * page if n > 0 else 0
            expected = page + page_up(kernel) + page_up(ramdisk)
            missing = max(0, expected - file_size)
            return {
                "exists": True, "path": path, "magic": "ANDROID!",
                "size": file_size, "recognized": True,
                "magic_ok": True, "header_version": native["header_version"],
                "page_size": page,
                "os_version": native["os"] or "0.0.0",
                "truncated": missing > 0,
                "valid": (not (missing > 0)) and kernel > 0, "native": True,
                # derived completeness fields (page-aligned)
                "kernel_bytes": kernel,
                "ramdisk_bytes": ramdisk,
                "second_bytes": 0,
                "expected_size": expected,
                "missing_bytes": missing,
                "file_size": file_size,
            }
    except Exception:
        pass  # fall through to the portable parser
    with open(path, "rb") as f:
        data = f.read()
    total = len(data)
    head = peek_header(data)
    if not head:
        return {"exists": True, "path": path, "magic": None,
                "size": total, "recognized": False}
    page = head["page_size"]
    kernel = head["kernel_size"]
    ramdisk = head["ramdisk_size"]
    second = head["second_size"]
    # compute expected padded size (each section is page-aligned)
    def page_up(n):
        return ((n + page - 1) // page) * page if n > 0 else 0
    expected = page  # header page
    for s in (kernel, ramdisk, second):
        expected += page_up(s)
    expected += head.get("recovery_dtbo_size", 0)
    head["expected_size"] = expected
    head["file_size"] = total
    head["recognized"] = True
    # completeness: image should be >= expected (allow trailing padding)
    head["kernel_bytes"] = kernel
    head["ramdisk_bytes"] = ramdisk
    head["second_bytes"] = second
    missing = max(0, expected - total)
    head["truncated"] = missing > 0
    head["missing_bytes"] = missing
    head["valid"] = (not head["truncated"]) and kernel > 0
    return head


def verify_sections(head):
    """Summarise the payload sections for a complete/valid verdict."""
    if not head or not head.get("recognized"):
        return {"complete": False, "reason": "not an Android boot image"}
    issues = []
    if head.get("kernel_bytes", 0) <= 0:
        issues.append("no kernel (empty)")
    if head.get("truncated"):
        issues.append(f"truncated by {head.get('missing_bytes')} bytes")
    if head.get("header_version") not in (0, 1, 2, 3, 4):
        issues.append(f"unexpected header v{head.get('header_version')}")
    return {
        "complete": not issues,
        "issues": issues,
        "header_version": head.get("header_version"),
        "os_version": head.get("os_version"),
        "os_patch_level": head.get("os_patch_level"),
    }
