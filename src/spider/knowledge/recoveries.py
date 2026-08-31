"""
SpiderLang Recovery Registry — understands EVERY recovery variant natively.

Every recovery family writes its per-device config as <prefix><codename>.mk
in the device tree (e.g. omni_a70q.mk for TWRP, ofox_a70q.mk for OrangeFox).
Spider reads all of them through the same universal .mk reader and maps them
into the board model, so there is NO format spider cannot understand.

Add a new recovery here in a couple of lines.
"""


class Recovery:
    def __init__(self, name, mk_prefix, flag_prefix, codename_mk_glob, aliases=(), description=""):
        self.name = name
        self.mk_prefix = mk_prefix            # e.g. "omni_" for TWRP
        self.flag_prefix = flag_prefix        # e.g. "TW_" for TWRP
        self.codename_mk_glob = codename_mk_glob  # glob for codename mk
        self.aliases = aliases
        self.description = description

    def matches_target(self, target):
        t = (target or "").lower()
        names = {self.name.lower(), self.mk_prefix.rstrip("_").lower(), *self.aliases}
        return t in names

    def __repr__(self):
        return f"<Recovery {self.name}>"


# The complete recovery ecosystem, in rough order of popularity.
RECOVERIES = [
    Recovery(
        "twrp", "omni_", "TW_", "omni_*.mk",
        aliases=("twrp", "omni"),
        description="Team Win Recovery Project — the de-facto standard (codename mk: omni_<device>.mk)",
    ),
    Recovery(
        "orangefox", "ofox_", "OF_", "ofox_*.mk",
        aliases=("ofox", "orange", "orange_fox", "orangefoxrecovery"),
        description="OrangeFox Recovery — MIUI/Xiaomi focused, themable (codename mk: ofox_<device>.mk)",
    ),
    Recovery(
        "pbrp", "pbrp_", "PBRP_", "pbrp_*.mk",
        aliases=("pitchblack", "pitch_black"),
        description="PitchBlack Recovery Project — feature-rich with its own flavour (codename mk: pbrp_<device>.mk)",
    ),
    Recovery(
        "shrp", "shrp_", "SHRP_", "shrp_*.mk",
        aliases=("skyhawk", "sky_hawk"),
        description="SkyHawk Recovery Project — rich feature set (codename mk: shrp_<device>.mk)",
    ),
    Recovery(
        "redwolf", "rw_", "RW_", "rw_*.mk",
        aliases=("red_wolf", "rw"),
        description="RedWolf Recovery — TWRP fork with extra tools (codename mk: rw_<device>.mk)",
    ),
    Recovery(
        "pitchblack", "pbrp_", "PBRP_", "pbrp_*.mk",  # alias of pbrp
    ),
    Recovery(
        "scratched", "scr_", "SCR_", "scr_*.mk",
        aliases=("scr",),
        description="Scratched Recovery (custom)",
    ),
    Recovery(
        "ctr", "ctr_", "CTR_", "ctr_*.mk",
        aliases=("ctrl",),
        description="ClockworkMod recovery custom (codename mk: ctr_<device>.mk)",
    ),
]


# Inverse lookup: file stem -> recovery  (e.g. ofox_a70q.mk -> orangefox)
def recovery_from_mk(filename):
    stem = (filename or "").lower()
    for r in RECOVERIES:
        # match <prefix><codename>.mk where prefix is the recovery mk_prefix
        for prefix in {r.mk_prefix, r.mk_prefix.upper()}:
            if stem.startswith(prefix) and stem.endswith(".mk"):
                return r
    return None


# Inverse lookup: any flag prefix -> recovery name
def recovery_from_flag(varname):
    v = (varname or "").upper()
    for r in RECOVERIES:
        if r.flag_prefix and v.startswith(r.flag_prefix):
            return r
    return None


def recovery_by_name(name):
    name = (name or "").lower()
    for r in RECOVERIES:
        if r.matches_target(name):
            return r
    return None


def all_recoveries():
    return RECOVERIES


def known_flag_for(recovery, varname):
    """Return a short human description for a known flag, else None."""
    v = varname.upper()
    KNOWN = {
        "TW": {
            "TW_HAS_MTP": "Media Transfer Protocol (MTP) enabled",
            "TW_INCLUDE_CRYPTO": "userdata decryption support",
            "TW_INCLUDE_CRYPTO_FBE": "file-based encryption support",
            "TW_INCLUDE_CRYPTO_FBE2": "FBE (v2) support",
            "TW_EXCLUDE_APEX": "exclude APEX from decryption",
            "TW_EXCLUDE_DEFAULT_USB_INIT": "no default usb init",
            "TW_BRIGHTNESS_PATH": "custom backlight sysfs path",
            "TW_MAX_BRIGHTNESS": "custom maximum brightness",
            "TW_DEFAULT_BRIGHTNESS": "default brightness value",
            "TW_EXTRA_LANGUAGES": "extra locale languages",
            "TW_USE_TOOLBOX": "use toybox toolbox",
            "TW_CUSTOM_CPU_TEMP_PATH": "custom CPU temperature path",
            "TW_CUSTOM_BATTERY_PATH": "custom battery path",
            "TW_INCLUDE_FUSE_EXFAT": "exFAT (FUSE) support",
            "TW_INCLUDE_FUSE_NTFS": "NTFS (FUSE) support",
            "TW_INCLUDE_NTFS_3G": "NTFS-3G binaries",
            "TW_INCLUDE_LIBUSB": "libusb (fastboot/ADB) support",
            "TW_CRYPTO_USE_SYSTEM_VOLD": "use system vold for crypto",
            "TW_NO_SCREEN_BLANK": "prevent screen blanking",
            "TW_THEME": "theme variant",
            "TW_INPUT_BLACKLIST": "blacklisted input devices",
            "TW_IGNORE_AB_DEVICE": "treat A/B device as non-A/B",
            "AB_OTA_UPDATER": "A/B OTA updater support",
            "PRODUCT_USE_DYNAMIC_PARTITIONS": "dynamic (super) partitions",
            "TARGET_IS_64_BIT": "64-bit userspace",
            "TW_SUPPORT_INSTALL_OPTAILS": "install options support",
            "TW_HAS_DOWNLOAD_MODE": "Samsung download mode present",
        },
        "OF": {
            "OF_USE_GREEN_LED_NOTIF": "green LED notification",
            "OF_USE_MAGISKBOOT": "magiskboot integration",
            "OF_USE_TWRP_SAR_DETECT": "SAR (system-as-root) detection",
            "OF_SUPPORT_ALL_BLOCK_OTA_UPDATES": "support all-block OTA",
            "OF_NO_RELOAD_AFTER_DECRYPTION": "no reload after decrypt",
            "OF_SCREEN_H": "screen height (pixels)",
            "OF_STATUS_H": "status bar height",
            "OF_STATUS_INDENT_LEFT": "status indent left",
            "OF_CLOCK_POS": "clock position",
            "OF_TWRP_COMPATIBILITY_MODE": "TWRP compatibility mode",
            "OF_ALLOW_DISABLE_NAVBAR": "allow navbar disable",
        },
        "PBRP": {
            "PBRP_BACKUP_MAX_STAT_SIZE": "max backup stat size",
            "PBRP_USE_YELLOW_TEXT": "yellow theme text",
            "PBRP_ADDITIONAL_SYSTEM_PROPS": "extra system properties",
            "PBRP_USE_DIALOG_STYLE": "dialog style UI",
        },
        "SHRP": {
            "SHRP_PATH": "SHRP install path",
            "SHRP_DEVICE_CODE": "SHRP device code",
            "SHRP_EDL_MODE": "EDL (Qualcomm) mode support",
            "SHRP_REC": "recovery variant",
            "SHRP_EXTERNAL": "external storage path",
            "SHRP_OTG": "OTG support",
            "SHRP_FLASH": "flash support",
            "SHRP_NOTCH": "notch display support",
            "SHRP_STATUSBAR_RIGHT_PADDING": "statusbar right padding",
            "SHRP_STATUSBAR_LEFT_PADDING": "statusbar left padding",
        },
    }
    table = KNOWN.get((recovery.flag_prefix or "TW").upper(), {})
    return table.get(v)


def flag_hint(varname):
    """Best-effort description regardless of recovery prefix."""
    v = varname.upper()
    for pref, table in {
        "TW": {
            "TW_HAS_MTP": "MTP enabled",
            "TW_INCLUDE_CRYPTO": "decryption support",
            "TW_EXCLUDE_APEX": "exclude APEX",
            "TW_EXCLUDE_DEFAULT_USB_INIT": "no default usb init",
            "TW_BRIGHTNESS_PATH": "backlight path",
            "TW_EXTRA_LANGUAGES": "extra languages",
            "TW_USE_TOOLBOX": "toybox toolbox",
            "TW_INCLUDE_FUSE_EXFAT": "exFAT support",
            "TW_INCLUDE_FUSE_NTFS": "NTFS support",
        },
        "OF": {
            "OF_USE_MAGISKBOOT": "magiskboot",
            "OF_SUPPORT_ALL_BLOCK_OTA_UPDATES": "all-block OTA",
            "OF_USE_GREEN_LED_NOTIF": "green LED notif",
            "OF_USE_TWRP_SAR_DETECT": "SAR detection",
        },
        "PBRP": {
            "PBRP_BACKUP_MAX_STAT_SIZE": "max stat size",
            "PBRP_USE_YELLOW_TEXT": "yellow text",
        },
        "SHRP": {
            "SHRP_EDL_MODE": "EDL mode",
            "SHRP_NOTCH": "notch display",
        },
    }.items():
        if v.startswith(pref):
            if v in table:
                return table[v]
            return f"{pref.rstrip('_')} flag"
    return None
