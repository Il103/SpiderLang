// Android.tm validator. Checks parsed modules against the known type table.
#pragma once
#include <string>
#include <vector>

#include "tm/ast.h"

namespace spider::tm {

enum class Severity { Ok, Warn, Fail };

struct Issue {
    Severity sev;
    std::string msg;
    int line = 0;
};

struct Result {
    std::vector<Issue> issues;
    int modules = 0;

    int count(Severity s) const {
        int n = 0;
        for (const auto& i : issues) if (i.sev == s) n++;
        return n;
    }
};

// Validate a parsed .tm file against the known module type table.
Result validate(const File& file);

}  // namespace spider::tm
