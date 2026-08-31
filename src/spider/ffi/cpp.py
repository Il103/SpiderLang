"""
FFI handler for C++
use cpp "path.cpp" as alias
For v0.1 we simulate compilation and provide mock verification.
In production, this would compile via g++ and load via ctypes/subprocess.
"""
import os, subprocess, pathlib
from .registry import register

@register("cpp")
class CppFFI:
    def load(self, module, full_path):
        # Simulate: check file exists, provide mock functions
        # Real implementation would do: g++ -shared -fPIC -o /tmp/lib.so full_path
        module.loaded = True
        # Common validator function used in BoardConfig example
        def verify_sizes(board):
            # board is dict from SpiderLang
            print(f"[{module.alias}] C++ validator: checking board {board}")
            # Example check: boot_partition_size should be multiple of kernel_pagesize
            try:
                boot_size = board.get("boot_partition_size") if isinstance(board, dict) else None
                # If board is bootloader sub-dict
                if isinstance(board, dict) and "boot_partition_size" in board:
                    boot_size = board["boot_partition_size"]
                from ..interpreter import SpiderSize
                if isinstance(boot_size, SpiderSize):
                    bs = boot_size.bytes
                elif isinstance(boot_size, int):
                    bs = boot_size
                else:
                    bs = 0
                if bs % 4096 == 0:
                    print(f"[{module.alias}] ✓ partition size {bs} is valid (4096 aligned)")
                    return True
                else:
                    print(f"[{module.alias}] ✗ partition size {bs} NOT aligned!")
                    return False
            except Exception as e:
                print(f"[{module.alias}] verify error: {e}")
                return False

        def add(a, b):
            return a + b

        module.functions["verify_sizes"] = verify_sizes
        module.functions["verify"] = verify_sizes
        module.functions["add"] = add

@register("c")
@register("cc")
class CAlias(CppFFI):
    pass
