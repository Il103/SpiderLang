"""
FFI handler for JavaScript (Node.js)
use js "app.js" as jsmod
"""
import subprocess, json, os
from .registry import register

@register("js")
@register("javascript")
@register("node")
class JsFFI:
    def load(self, module, full_path):
        module.loaded = True
        def call_js(func, *args):
            # Simulate Node call via subprocess if node exists
            # For demo, just mock
            print(f"[{module.alias}] JS call {func}({args}) from {full_path} (mock)")
            return f"js:{func}({args})"
        # Provide generic caller
        module.functions["call"] = call_js
        # Provide example functions
        module.functions["run"] = lambda *a: call_js("run", *a)
        module.functions["predict"] = lambda *a: f"js predict mock {a}"

@register("rust")
class RustStub:
    def load(self, module, full_path):
        module.loaded = True
        module.functions["call"] = lambda *a: print(f"[{module.alias}] Rust mock {a}")

@register("go")
class GoStub:
    def load(self, module, full_path):
        module.loaded = True
        module.functions["call"] = lambda *a: print(f"[{module.alias}] Go mock {a}")

@register("java")
class JavaStub:
    def load(self, module, full_path):
        module.loaded = True
        module.functions["call"] = lambda *a: print(f"[{module.alias}] Java mock {a}")
