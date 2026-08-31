#include "tm/validate.h"

#include <set>

namespace spider::tm {

namespace {

// The .tm module type table the chip understands. Each type names its
// required properties and what it actually builds (so the validator can warn
// when a type is clearly missing the thing it produces).
struct TypeSpec {
    std::vector<std::string> required;
    const char* builds = "";
};

const std::map<std::string, TypeSpec>& specTable() {
    static const std::map<std::string, TypeSpec> table = {
        {"cc_binary",         {{"srcs"}, "an executable"},                 },
        {"cc_library",        {{"srcs"}, "a static or shared library"},    },
        {"cc_defaults",       {{{}}, ""                                  }},
        {"build",             {{"target"}, "a device image"},             },
        {"device",            {{"board"}, "a device definition"},         },
        {"recovery",          {{"variant" }, "a recovery image"},         },
        {"image",             {{"kind" }, "a boot/recovery image"},       },
        {"scripts",           {{{}}, "a set of scripts"},                 },
    };
    return table;
}

std::string valueText(const ValuePtr& v) {
    if (!v) return "";
    switch (v->kind) {
        case Value::Kind::Str:  return "\"" + v->str_ + "\"";
        case Value::Kind::Num:  return std::to_string((long)v->num_);
        case Value::Kind::Bool: return v->bool_ ? "true" : "false";
        case Value::Kind::List: {
            std::string s = "[";
            for (size_t i = 0; i < v->list_.size(); i++) {
                if (i) s += ", ";
                s += valueText(v->list_[i]);
            }
            return s + "]";
        }
        case Value::Kind::Block: return "{...}";
    }
    return "";
}

std::vector<std::string> strList(const ValuePtr& v) {
    std::vector<std::string> out;
    if (!v || v->kind != Value::Kind::List) return out;
    for (const auto& e : v->list_)
        if (e->kind == Value::Kind::Str) out.push_back(e->str_);
    return out;
}

}  // namespace

Result validate(const File& file) {
    Result r;
    r.modules = static_cast<int>(file.modules.size());
    const auto& table = specTable();
    std::set<std::string> moduleNames;

    for (const auto& m : file.modules) {
        if (!m.name.empty()) {
            if (moduleNames.count(m.name)) {
                r.issues.push_back({Severity::Fail,
                    "duplicate module name '" + m.name + "'", m.line});
            }
            moduleNames.insert(m.name);
        }

        auto it = table.find(m.type);
        if (it == table.end()) {
            r.issues.push_back({Severity::Warn,
                "unknown module type '" + m.type + "' (chip doesn't know it yet)", m.line});
            continue;
        }
        const TypeSpec& spec = it->second;
        if (spec.builds[0]) {
            r.issues.push_back({Severity::Ok,
                "module '" + (m.name.empty() ? "<anon>" : m.name) +
                "' (" + m.type + ") describes " + spec.builds, m.line});
        }
        for (const auto& req : spec.required) {
            if (!req.empty() && !m.byName.count(req)) {
                r.issues.push_back({Severity::Fail,
                    "module '" + m.name + "' (" + m.type +
                    ") is missing required property '" + req + "'", m.line});
            }
        }
    }
    return r;
}

}  // namespace spider::tm
