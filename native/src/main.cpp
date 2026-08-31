// SpiderLang Native — Main (C++ From Scratch)
// This binary will replace the Python bootstrap in v0.2
// Currently scaffold — demonstrates native build intent.
// Usage: ./spider run file.spt  (future)
// For now, delegates to Python bootstrap.

#include <iostream>
#include <string>

const char* SPIDER_ASCII = R"(
      / _ \   SpiderLang Native v0.2 — C++ From Scratch
    \_\(_)/_/  Created by Beru
     _//"\\_   No Python trace — pure binary
      /   \
     /\/\/\   🕷️  Universal FFI • Native Build
    /      \
    \__/\__/
)";

int main(int argc, char* argv[]) {
    std::cout << SPIDER_ASCII << "\n";
    if (argc < 2) {
        std::cout << "Usage: spider <run|lunch|build> [args]\n";
        std::cout << "Native C++ port is in progress. For now, use: PYTHONPATH=src python3 -m spider ...\n";
        return 0;
    }
    std::string cmd = argv[1];
    std::cout << "Native command '" << cmd << "' — forwarding to bootstrap (v0.1 Python) until C++ VM is complete.\n";
    std::cout << "Track progress: native/src/lexer.cpp ✓, parser.cpp ⏳, interpreter.cpp ⏳\n";
    return 0;
}
