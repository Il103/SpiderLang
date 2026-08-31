# ofox_a70q.mk — OrangeFox Recovery device makefile for Samsung Galaxy A70
# This is a REAL Android makefile. Spider reads it natively (no conversion).

# inherit the common OrangeFox stuff
$(call inherit-product, vendor/fox/config/common.mk)

# Device code
TARGET_DEVICE := a70q
TARGET_PRODUCT := ofox_a70q
PRODUCT_NAME := ofox_a70q

# OrangeFox specific flags
OF_USE_GREEN_LED_NOTIF := true
OF_USE_TWRP_SAR_DETECT := true
OF_SUPPORT_ALL_BLOCK_OTA_UPDATES := true
OF_USE_MAGISKBOOT := true
OF_NO_RELOAD_AFTER_DECRYPTION := true
OF_SCREEN_H := 2400
OF_STATUS_H := 100
OF_CLOCK_POS := 2

# TWRP compatibility flags (OrangeFox keeps these too)
TW_THEME := portrait_hdpi
TW_INCLUDE_CRYPTO := true
TW_INCLUDE_CRYPTO_FBE := true
TW_HAS_MTP := true
TW_INCLUDE_FUSE_EXFAT := true
TW_EXCLUDE_DEFAULT_USB_INIT := false

# A/B partitions for this device
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# extra packages
PRODUCT_PACKAGES += \
    ofox_super_image \
    espresso
