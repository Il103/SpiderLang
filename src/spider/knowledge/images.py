"""
SpiderLang Image Formats — the language's knowledge of every boot image type
(recovery.img, boot.img, vendor_boot.img), each with its full flag set and
header layout, so ANY device / SoC build works out of the box.

This is language domain-knowledge (like recoveries.py and the SIZE_UNITS),
not a per-file script.
"""


class ImageType:
    RED_BG = "\033[31m"
    GREEN_BG = "\033[32m"
    YELLOW_BG = "\033[33m"
    BLUE_BG = "\033[34m"
    MAGENTA_BG = "\033[35m"
    CYAN_BG = "\033[36m"

    def __init__(self, name, ext, color, tag, header_ver, descriptions, moniker, blurb="", flags=()):
        self.name = name            # e.g. "boot"
        self.ext = ext              # e.g. "boot.img"
        self.color = color
        self.tag = tag              # short tag for display
        self.header_ver = header_ver
        self.descriptions = descriptions   # dict flag -> meaning
        self.moniker = moniker
        self.blurb = blurb
        self.flags = flags          # ordered flag names for display

    def __repr__(self):
        return f"<ImageType {self.name} {self.ext}>"


BOOT_COMMON = {
    "kernel": "kernel image path (Image.gz / Image.gz-dtb)",
    "ramdisk": "ramdisk (boot ramdisk) path/type",
    "cmdline": "kernel command line",
    "base": "kernel load base address",
    "kernel_offset": "kernel load offset",
    "ramdisk_offset": "ramdisk load offset",
    "tags_offset": "tags load offset",
    "second": "second-stage bootloader image",
    "dtb": "device tree blob appended/embedded",
    "dtbo": "device tree overlay image",
    "os_version": "OS version packed in header",
    "os_patch_level": "OS security patch level",
    "arch": "target architecture",
    "pagesize": "page size (2048/4096)",
    "board_id": "board identification array",
    "header_version": "boot image header version (0/1/2/3/4)",
    "extra_cmdline": "extra command line tokens",
    "recovery_dtbo": "recovery dtbo image",
    "recovery_acpio": "recovery acpio image",
    "bootconfig": "bootconfig file for header v3+",
    "vendor_boot_ramdisk": "extra vendor ramdisk in vendor_boot",
}


def _flags(*names):
    return names


IMAGE_TYPES = [
    ImageType(
        "boot", "boot.img", "\033[32m", "BOOT", "0-4",
        BOOT_COMMON,
        "Legacy / A/B kernel-boot image",
        blurb="kernel + boot-ramdisk packed in a single image",
        flags=_flags("kernel", "ramdisk", "cmdline", "base", "dtb", "dtbo",
                     "os_version", "os_patch_level", "pagesize", "header_version",
                     "kernel_offset", "ramdisk_offset", "tags_offset", "bootconfig"),
    ),
    ImageType(
        "recovery", "recovery.img", "\033[31m", "RECOVERY", "0-2",
        {
            **BOOT_COMMON,
            "recovery_dtbo": "recovery device-tree overlay",
            "recovery_acpio": "recovery ACPI table",
            "twrp_flags": "TWRP feature flags applied to the image",
            "of_flags": "OrangeFox feature flags applied to the image",
            "max_bytes": "maximum allowed recovery partition size",
            "ramdisk_type": "recovery ramdisk type (recovery-ramdisk)",
        },
        "Recovery ramdisk image (TWRP/OF/PBRP/SHRP...)",
        blurb="recovery.img — what spider build produces by default",
        flags=_flags("kernel", "ramdisk", "cmdline", "base", "recovery_dtbo",
                     "recovery_acpio", "dtbo", "os_version", "max_bytes",
                     "ramdisk_type", "twrp_flags", "of_flags"),
    ),
    ImageType(
        "vendor_boot", "vendor_boot.img", "\033[34m", "VENDORBOOT", "3-4",
        {
            **BOOT_COMMON,
            "vendor_boot_ramdisk": "vendor ramdisk(s) embedded in vendor_boot",
            "vendor_ramdisk_fragment": "vendor ramdisk fragment (header v4)",
            "vendor_cmdline": "vendor command line (header v3+)",
            "vendor_bootconfig": "vendor bootconfig (header v4)",
            "vendor_dtb": "vendor device tree blob",
            "vendor_dtb_offset": "vendor dtb load offset",
            "header_v3_v4": "vendor_boot header version 3 or 4",
            "bootconfig_mtu": "bootconfig size limit",
            "qpkg": "Qualcomm DTBO/QDTC vendor boot magic",
            "balloon": "vendor boot header size",
        },
        "Vendor boot image (A/B, header v3/v4)",
        blurb="boot.img with the kernel; vendor_boot.img carries the vendor ramdisk",
        flags=_flags("vendor_boot_ramdisk", "vendor_ramdisk_fragment",
                     "vendor_cmdline", "vendor_bootconfig", "vendor_dtb",
                     "vendor_dtb_offset", "header_v3_v4", "kernel", "dtbo",
                     "bootconfig"),
    ),
]


def by_name(name):
    n = (name or "").lower()
    for it in IMAGE_TYPES:
        if n in (it.name, it.ext, it.ext.replace(".img", "")):
            return it
    return None


def image_kinds():
    return [it.name for it in IMAGE_TYPES]


def flag_meaning(image, flag):
    it = by_name(image)
    if not it:
        return None
    # strip common prefix to look up
    for k, v in it.descriptions.items():
        if flag.lower() == k.lower():
            return v
    return None
