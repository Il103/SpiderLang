"""
SpiderLang knowledge — everything the language natively understands about the
Android ecosystem: every recovery, every boot/recovery image, Soong (.bp) build
rules, and the hidden magiskboot tool — all read by the language itself.
"""
from .recoveries import (
    Recovery, RECOVERIES, recovery_from_mk, recovery_from_flag,
    recovery_by_name, all_recoveries, known_flag_for, flag_hint,
)
from .images import IMAGE_TYPES, by_name as image_by_name, image_kinds

__all__ = ["Recovery", "RECOVERIES", "recovery_from_mk", "recovery_from_flag",
           "recovery_by_name", "all_recoveries", "known_flag_for", "flag_hint",
           "IMAGE_TYPES", "image_by_name", "image_kinds"]
