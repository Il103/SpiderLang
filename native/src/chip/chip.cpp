#include "chip/chip.h"

#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <unistd.h>

#include "util/fs.h"

namespace spider::chip {

namespace {
// Locate the magiskboot matching the current ABI. Order: x86_64, x86, arm64,
// arm. We prefer the native build of the host OS when present.
void probeAbis(std::vector<std::string>& abis) {
#if defined(__x86_64__) || defined(_M_X64)
    abis = {"x86_64", "x86", "arm64", "arm"};
#elif defined(__aarch64__)
    abis = {"arm64", "x86_64", "x86", "arm"};
#elif defined(__arm__)
    abis = {"arm", "arm64", "x86_64", "x86"};
#else
    abis = {"x86_64", "x86", "arm64", "arm"};
#endif
}
}  // namespace

std::string magiskbootPath() {
    static std::string cached;
    if (!cached.empty()) return cached;

    std::vector<std::string> abis;
    probeAbis(abis);

    // try relative to cwd first
    for (const auto& abi : abis)
        if (fs::exists("chip/" + abi + "/magiskboot"))
            return cached = "chip/" + abi + "/magiskboot";

    // walk up from the running executable looking for a chip/ directory
    std::string self = "/proc/self/exe";
    char link[4096];
    ssize_t n = readlink(self.c_str(), link, sizeof(link) - 1);
    if (n > 0) {
        link[n] = '\0';
        std::string dir = std::string(link).substr(0, std::string(link).find_last_of('/'));
        while (true) {
            for (const auto& abi : abis) {
                std::string p = dir + "/chip/" + abi + "/magiskboot";
                if (fs::exists(p)) return cached = p;
            }
            auto slash = dir.find_last_of('/');
            if (slash == std::string::npos || slash == 0) break;
            dir = dir.substr(0, slash);
        }
    }
    return "";
}

int runMagiskboot(const std::vector<std::string>& args, std::string& out) {
    std::string bin = magiskbootPath();
    if (bin.empty()) {
        out = "chip: magiskboot not bundled";
        return 127;
    }
    // stdout+stderr into a temp file, then read back
    std::string tmp = "/tmp/spider-chip-XXXXXX";
    char* t = tmp.data();
    int fd = mkstemp(t);
    if (fd < 0) {
        out = "chip: could not create temp output";
        return 125;
    }
    (void)fd;
    // build command line (quote the binary path too — it may contain spaces)
    std::string cmd;
    if (bin.find(' ') != std::string::npos) cmd = "\"" + bin + "\"";
    else cmd = bin;
    for (const auto& a : args) {
        cmd += " ";
        if (a.find(' ') != std::string::npos) cmd += "\"" + a + "\"";
        else cmd += a;
    }
    cmd += " > " + tmp + " 2>&1";
    int rc = system(cmd.c_str());
    std::string content;
    fs::readFile(tmp, content);
    out = content;
    std::remove(tmp.c_str());
    if (rc < 0) return 126;
    return rc == 0 ? 0 : 1;
}

Header peek(const std::string& imgPath, long fileSize) {
    (void)fileSize;
    Header h;
    std::ifstream in(imgPath, std::ios::binary);
    unsigned char buf[2048];
    in.read(reinterpret_cast<char*>(buf), sizeof(buf));
    std::streamsize got = in.gcount();
    const unsigned char magic[8] = {'A','N','D','R','O','I','D','!'};
    if (got < 64 || std::memcmp(buf, magic, 8) != 0) return h;  // not an android image

    h.valid = true;
    // AOSP boot header v0+ layout:
    // 36: page_size (u32 LE)   40: header_version (u32 LE)   44: os_version (u32 LE)
    auto u32 = [&](size_t off) -> unsigned {
        return (unsigned)buf[off] | ((unsigned)buf[off+1] << 8) |
               ((unsigned)buf[off+2] << 16) | ((unsigned)buf[off+3] << 24);
    };
    h.pageSize = u32(36);
    h.version = (int)u32(40);
    unsigned osv = u32(44);
    // os_version: high 8 bits major, next 8 minor, remaining patch
    int major = (osv >> 25) & 0x7F;
    int minor = (osv >> 18) & 0x7F;
    int patch = (osv >> 11) & 0x7F;
    h.os = std::to_string(major) + "." + std::to_string(minor) + "." + std::to_string(patch);

    long page = h.pageSize > 0 ? (long)h.pageSize : 2048;
    unsigned kernelSize = u32(8);
    unsigned ramdiskSize = u32(16);
    h.kernelBytes = (long)kernelSize;
    h.ramdiskBytes = (long)ramdiskSize;
    unsigned secondSize = u32(28);       // v0
    unsigned dtbSize = (h.version >= 2) ? u32(1436) : 0;
    unsigned recoveryDtboSize = (h.version == 1 || h.version == 2) ? u32(1432) : 0;
    // declared = header + padded sections
    long header = (h.version == 0) ? (long)page * 1
                 : (h.version == 1) ? (long)page * 2
                 : (h.version == 2) ? (long)page * 3
                 : (h.version == 3) ? 4096 : (long)page * 4;
    auto align = [&](long v) { return (v + page - 1) / page * page; };
    long declared = header
        + align(kernelSize)
        + align((long)ramdiskSize);
    if (secondSize) declared += align(secondSize);
    if (dtbSize) declared += align(dtbSize);
    if (recoveryDtboSize) declared += align(recoveryDtboSize);
    h.declaredSize = declared;
    return h;
}

}  // namespace spider::chip
