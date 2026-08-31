// Bundled tool helpers: locating/running the shipped magiskboot binaries and
// a small boot-header reader used for instant image checks.
#pragma once
#include <string>
#include <vector>

namespace spider::chip {

// Full path to the recovered-ABI magiskboot binary shipped in native/chip/.
// Returns an empty string if it can't be located.
std::string magiskbootPath();

// Run the bundled magiskboot with the given args. Returns its exit code.
// Leaves the full output in `out`.
int runMagiskboot(const std::vector<std::string>& args, std::string& out);

// Boot-image header summary (fast native peek, no subprocess needed).
struct Header {
    bool valid = false;   // ANDROID! magic present
    int version = 0;      // header version (0..4)
    long pageSize = 0;
    std::string os;       // "13.0.0"
    long kernelBytes = 0;
    long ramdiskBytes = 0;
    // page-aligned expected length from header fields vs actual file size
    long declaredSize = 0;
};
// Quick header read of a boot/recovery image. does not require magiskboot.
Header peek(const std::string& imgPath, long fileSize);

}  // namespace spider::chip
