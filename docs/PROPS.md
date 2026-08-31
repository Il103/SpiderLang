# Props — .prop native understanding

`system.prop` / `vendor.prop` / `product.prop` / `odm.prop` etc. keep their **own extension** `.prop` — Spider reads them natively, like `fstab` and `Android.tm`.

## Grammar

```
# comment  or  ! comment
import /system/etc/prop.cfg

ro.hardware=mt6789
ro.build.product=X6886
ro.postinstall.fstab.prefix=/system
keymaster_ver=4.1
ro.vendor.mtk_tee_gp_support=1
```

- `key=value` (spaces allowed: `key = value`)
- `key:value` also accepted
- last value wins (Android behavior)
- quotes around value are stripped: `ro.foo="bar" -> bar`

## What the language understands

- `understand("device/infinix/X6886")` returns `props: { "system.prop": {props:{}, total:7} }`
- `props("system.prop")` builtin — hidden capability like `magiskboot()` and `soong()`
- `spider check` verifies essential props: `ro.hardware, ro.board.platform, ro.build.product/device, ro.product.device`

## Example

```spider
let p = props("system.prop")
print(p["ro.hardware"]) // mt6789
print(p.total) // 7
```

The format stays `.prop` — the code is dedicated.
