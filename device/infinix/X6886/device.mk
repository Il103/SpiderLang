// device.mk — product definition for X6886 (Spider native)
// Declares what gets installed into the recovery ramdisk.

product {
    name: "twrp_X6886",
    arch: "arm64",
    device: "infinix/X6886",

    packages: [
        "recovery",
        "libtwrpcompat",
        "twrpdecrypt",
    ],

    recovery_fstab: "recovery.fstab",
}
