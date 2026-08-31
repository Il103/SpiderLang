"""
FFI handler for Python
use python "path.py" as alias
Calls Python functions natively.
"""
import importlib.util, os
from .registry import register

@register("python")
class PythonFFI:
    def load(self, module, full_path):
        spec = importlib.util.spec_from_file_location(module.alias, full_path)
        if not spec or not spec.loader:
            module.error = f"Cannot load Python file {full_path}"
            return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in dir(mod):
            if not name.startswith("_"):
                attr = getattr(mod, name)
                module.functions[name] = attr
        module.loaded = True

@register("py")
class PyAlias(PythonFFI):
    pass
