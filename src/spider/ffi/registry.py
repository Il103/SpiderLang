"""
SpiderLang FFI Registry — Plugin architecture
Each language lives in src/spider/ffi/<lang>.py
Add a new language in ~20 lines.
"""

handlers = {}

def register(lang):
    def decorator(cls):
        handlers[lang.lower()] = cls()
        return cls
    return decorator

def get(lang):
    return handlers.get(lang.lower())

# Auto-import all ffi modules
import os, importlib, pathlib
ffi_dir = pathlib.Path(__file__).parent
for f in ffi_dir.glob("*.py"):
    if f.name in ("registry.py", "__init__.py"):
        continue
    mod_name = f"src.spider.ffi.{f.stem}"
    # try import as package spider.ffi.<lang>
    try:
        import importlib.util
        # alternative: try import by path
        pkg = f"spider.ffi.{f.stem}"
        try:
            importlib.import_module(pkg)
        except:
            # fallback load from file
            spec = importlib.util.spec_from_file_location(pkg, str(f))
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
    except Exception as e:
        print(f"[ffi] failed to load {f.name}: {e}")
