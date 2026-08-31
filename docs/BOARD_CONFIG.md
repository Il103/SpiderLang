# BoardConfig.spt — Complete Reference

Replaces `BoardConfig.mk` with SpiderLang's typed DSL.

## Why .spt?

| BoardConfig.mk | BoardConfig.spt |
|----------------|-----------------|
| `BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864` | `boot_partition_size: 64.MB` |
| No type, easy to miscount zeros | Typed, validated, `64.MB == 65536.KB == 67108864.B` |
| `:=` and `$(DEVICE_PATH)` mess | Clean `key: value` + `board { }` DSL |
| No logic | `if` + FFI + functions |
| Only Make | Native Spider build (no mk) |

## Full Example

```spider
board {
    arch: "arm64",
    arch_variant: "armv8-a",
    cpu_abi: "arm64-v8a",
    cpu_variant: "cortex-a55",

    bootloader: {
        board_name: "X6886",
        kernel_pagesize: 4096,
        boot_partition_size: 64.MB,
        recovery_partition_size: 64.MB,
        vendor_boot_size: 32.MB,
        super_partition_size: 9128.MB
    },

    kernel: {
        base: "0x40078000",
        cmdline: "bootopt=64S3,32N2,64N2",
        image_name: "Image.gz",
        separated_dtbo: true,
        header_version: 2
    },

    recovery: {
        type: "twrp", // twrp | orangefox | pbrp | shrp
        theme: "portrait_hdpi",
        include_crypto: true,
        include_crypto_fbe: true,
        flags: ["TW_EXCLUDE_APEX", "TW_HAS_MTP"]
    },

    partitions: {
        has_large_filesystem: true,
        system_type: "ext4",
        use_f2fs: true
    },

    avb: { enable: true },
    security: { platform_version: "14.0.0" }
}

use cpp "validators/partition_check.cpp" as checker
checker.verify_sizes(board.bootloader)
```

## All Supported TWRP Flags

Any flag can be used in `recovery.flags` list — SpiderLang doesn't hardcode, it's extensible:

```
TW_EXCLUDE_APEX
TW_HAS_MTP
TW_INCLUDE_CRYPTO
TW_INCLUDE_CRYPTO_FBE
TW_BRIGHTNESS_PATH
TW_MAX_BRIGHTNESS
TW_EXCLUDE_DEFAULT_USB_INIT
TW_EXCLUDE_MTP
TW_NO_REBOOT_BOOTLOADER
TW_USE_TOOLBOX
TW_INCLUDE_NTFS_3G
TW_EXTRA_LANGUAGES
TW_THEME
TW_DEVICE_VERSION
RECOVERY_SDCARD_ON_DATA
BOARD_HAS_LARGE_FILESYSTEM
... and 100+ more — just add to flags list
```

## Size Units (Binary 1024)

```
1.B  = 1
1.KB = 1024.B
1.MB = 1024.KB
1.GB = 1024.MB
1.TB = 1024.GB
1.PB = 1024.TB
1.EB = 1024.PB

64.MB == 65536.KB == 67108864.B == 0.0625.GB // all true
```

Use `.to("KB")` to convert: `64.MB.to("KB") == 65536`
