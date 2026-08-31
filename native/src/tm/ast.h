// SpiderLang Native — Android.tm AST
// A .tm "module" is a named build unit with a type and ordered properties.
#pragma once
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace spider::tm {

struct Value;
using ValuePtr = std::shared_ptr<Value>;
using PropList = std::vector<std::pair<std::string, ValuePtr>>;
using PropMap = std::map<std::string, ValuePtr>;

struct Value {
    enum class Kind { Str, Num, Bool, List, Block };
    Kind kind;
    std::string str_;
    double num_ = 0;
    bool bool_ = false;
    std::vector<ValuePtr> list_;
    PropList block_;
};

struct Module {
    std::string name;      // module identifier or ""
    std::string type;      // "cc_binary", "build", ...
    int line, col;
    PropList props;        // ordered
    PropMap byName;        // fast lookup
};

struct File {
    std::vector<Module> modules;
};

}  // namespace spider::tm
