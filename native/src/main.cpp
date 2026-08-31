// Native tools: Android.tm build validation + boot image header checks.
// Single binary, no external dependencies. Build with `make` in native/.
#include <unistd.h>

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "chip/chip.h"
#include "tm/ast.h"
#include "tm/lexer.h"
#include "tm/parser.h"
#include "tm/validate.h"
#include "util/fs.h"

using namespace spider;

static const char* BANNER =
    "       / \\_        SpiderLang tools\n"
    "     _\\\\(_)/_/\n"
    "      _//\"\\\\_    Android.tm validation\n"
    "        /   \\\n"
    "       /\\/\\/\\    boot image checks\n"
    "       \\__/ \n";

static void usage() {
    std::cout <<
        "usage: spider <command> [args]\n"
        "\n"
        "  tm <file.tm>            parse + validate an Android.tm build file\n"
        "  check <image> [size]    verify a boot/recovery image header\n"
        "  chip <magisk args...>   run the bundled magiskboot\n"
        "  info                    show bundled magiskboot presence & ABI\n"
        "  version                 print the version\n";
}

static int cmd_tm(const std::string& path) {
    std::string src;
    if (!fs::readFile(path, src)) {
        std::cerr << "chip: cannot read " << path << "\n";
        return 1;
    }
    tm::Lexer lex(src);
    auto toks = lex.scan();
    tm::Parser parser(std::move(toks), path);
    tm::File file;
    try {
        file = parser.parse();
    } catch (const tm::ParseError& e) {
        std::cerr << path << ":" << e.line << ":" << e.col
                  << "  parse error: " << e.msg << "\n";
        return 1;
    }
    tm::Result r = tm::validate(file);
    std::cout << "chip: " << path
              << "  ->  " << r.modules << " module(s)\n";
    for (const auto& i : r.issues) {
        std::string tag;
        switch (i.sev) {
            case tm::Severity::Ok:   tag = "ok";   break;
            case tm::Severity::Warn: tag = "warn"; break;
            case tm::Severity::Fail: tag = "FAIL"; break;
        }
        std::cout << "      [" << tag << "] " << i.msg << "\n";
    }
    int fails = r.count(tm::Severity::Fail);
    if (fails) {
        std::cerr << "chip: " << fails << " hard error(s) in " << path << "\n";
        return 1;
    }
    std::cout << "chip: verdict OK\n";
    return 0;
}

static int cmd_check(const std::string& img, const std::string& sizeArg) {
    long want = -1;
    if (!sizeArg.empty()) want = std::stol(sizeArg);

    std::ifstream in(img, std::ios::binary | std::ios::ate);
    if (!in) { std::cerr << "chip: cannot open " << img << "\n"; return 1; }
    long fileSize = (long)in.tellg();

    chip::Header h = chip::peek(img, fileSize);
    std::cout << "chip: " << img << "  (" << fileSize << " bytes)\n";
    if (!h.valid) {
        std::cout << "      [FAIL] not an Android boot/recovery image "
                     "(no ANDROID! magic)\n";
        return 1;
    }
    std::cout << "      [ok]   magic ANDROID! present\n";
    std::cout << "      [ok]   header v" << h.version
              << "   page_size " << h.pageSize
              << "   OS " << h.os
              << "   kernel " << h.kernelBytes
              << " ramdisk " << h.ramdiskBytes << "\n";
    bool truncated = (want > 0) ? (fileSize < want) : (h.declaredSize > fileSize);
    std::cout << "      [" << (truncated ? "FAIL" : "ok") << "]   "
              << (truncated ? "image looks truncated" : "image not truncated")
              << " (declared ~" << h.declaredSize << ")\n";
    if (want > 0) {
        std::cout << "      [info] expected " << want << " (from device tree)\n";
    }
    return truncated ? 1 : 0;
}

static int cmd_chip(std::vector<std::string> args) {
    std::string bin = chip::magiskbootPath();
    if (bin.empty()) {
        std::cerr << "chip: no bundled magiskboot found\n";
        return 127;
    }
    std::string out;
    chip::runMagiskboot(args, out);
    std::cout << out;
    return 0;
}

static int cmd_info() {
    std::string bin = chip::magiskbootPath();
    std::string abi = "unknown";
    if (!bin.empty()) {
        auto parts = fs::split(bin, '/');
        abi = parts.size() >= 3 ? parts[parts.size() - 2] : "?";
    }
    std::cout << "chip: magiskboot  " << (bin.empty() ? "MISSING" : "bundled")
              << "  [abi " << abi << "]\n";
    return bin.empty() ? 1 : 0;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cout << BANNER << "\n"; usage(); return 0; }
    std::string cmd = argv[1];

    if (cmd == "tm") {
        if (argc < 3) { std::cerr << "chip: tm needs a file\n"; return 1; }
        return cmd_tm(argv[2]);
    }
    if (cmd == "check") {
        if (argc < 3) { std::cerr << "chip: check needs an image\n"; return 1; }
        std::string size = argc >= 4 ? argv[3] : "";
        return cmd_check(argv[2], size);
    }
    if (cmd == "chip") {
        std::vector<std::string> args;
        for (int i = 2; i < argc; i++) args.push_back(argv[i]);
        return cmd_chip(args);
    }
    if (cmd == "info") return cmd_info();
    if (cmd == "version") { std::cout << "SpiderLang chip v3.0\n"; return 0; }
    if (cmd == "help" || cmd == "-h" || cmd == "--help") { usage(); return 0; }

    std::cerr << "chip: unknown command '" << cmd << "'\n";
    usage();
    return 1;
}
