# omni_X6886.mk — TWRP device makefile for Infinix Hot 40 Pro (X6886)
# Real Android makefile — Spider reads it natively (no conversion).

$(call inherit-product, vendor/twrp/config/common.mk)

TARGET_DEVICE := X6886
TARGET_PRODUCT := twrp_X6886
PRODUCT_NAME := twrp_X6886

# TWRP flags
TW_THEME := portrait_hdpi
TW_INCLUDE_CRYPTO := true
TW_INCLUDE_CRYPTO_FBE := true
TW_INCLUDE_CRYPTO_FBE2 := true
TW_HAS_MTP := true
TW_INCLUDE_FUSE_EXFAT := true
TW_INCLUDE_FUSE_NTFS := true
TW_EXCLUDE_APEX := true
TW_USE_TOOLBOX := true
TW_BRIGHTNESS_PATH := /sys/class/leds/lcd-backlight/brightness
TW_MAX_BRIGHTNESS := 2047
TW_DEFAULT_BRIGHTNESS := 900

# Newer devices need these for dynamic partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true
AB_OTA_UPDATER := true

# recovery ramdisk packages
PRODUCT_PACKAGES += \
    twrp \
    libtwrpcompat \
    twrpdecrypt
