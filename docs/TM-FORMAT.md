# Android.tm — the build-definition format

`.tm` (`Android.tm`) is Spider's own build-definition format — the successor to
Soong / `Android.bp`. It is parsed *natively* by the chip (no Python, no Soong
toolchain). It keeps the ideas builders love (sane module type checks, required
properties) with a clean, validation-friendly grammar.

## Grammar

A `.tm` file holds zero or more modules:

```
module <name> type <type> {
    <property>: <value>,
    ...
}
```

- `<name>` — an identifier or `"quoted string"`.
- `<type>` — a module type the chip understands (`cc_binary`, `cc_library`,
  `recovery`, `build`, `device`, `image`, ...).
- `<value>` — a string, number, `true`/`false`, a `[ ... ]` list, or a `{ ... }`
  block.
- Line / block comments: `//` and `/* ... */`.

## Example

```
// TWRP recovery (OrangeFox style) + a shared library
module "control_server" type "cc_binary" {
    srcs: ["main.cpp", "server.cpp"],
    deps: ["libcore"],
    static_libs: ["libz"],
    ndk_platform: "android-30",
}

module "libcore" type "cc_library" {
    srcs: ["core/a.cpp", "core/b.cpp"],
}

module "rom" type "recovery" {
    variant: "orangefox",
    target: "recovery",
}
```

## What the chip checks

- **parse** — a malformed file (unterminated list, missing `:` or `{`) is a hard
  error with `file:line:col`.
- **duplicate module names** — hard error.
- **unknown module type** — warning (chip doesn't know it yet).
- **missing required properties** — hard error (e.g. a `recovery` without
  `variant`, a `cc_binary` without `srcs`).

## Using it

```
# validate a file
spider tm Android.tm

# same, through the Python host (comes back as data)
python3 -c "from spider.chip import chip_tm; print(chip_tm('Android.tm'))"
```

The format is the project's own; it is not a re-encoding of `.bp`.
