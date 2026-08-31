// validators/partition_check.cpp — SpiderLang FFI example
// Called via: use cpp "validators/partition_check.cpp" as checker
//             checker.verify_sizes(board.bootloader)
#include <iostream>
#include <string>

// Simulated validator - in production this would be compiled
bool verify_sizes(void* board) {
    // Checks if boot_partition_size % kernel_pagesize == 0
    std::cout << "[cpp] verify_sizes: checking partition alignment..." << std::endl;
    return true;
}
