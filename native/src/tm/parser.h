// SpiderLang Native — Android.tm Parser
// Recursive-descent over the token stream; builds a File of modules.
#pragma once
#include <memory>
#include <string>

#include "tm/ast.h"
#include "tm/lexer.h"

namespace spider::tm {

struct ParseError {
    std::string msg;
    int line, col;
};

class Parser {
public:
    Parser(std::vector<Token> toks, std::string file)
        : toks_(std::move(toks)), file_(std::move(file)) {}

    // Throws ParseError on malformed input.
    File parse();

private:
    std::vector<Token> toks_;
    std::string file_;
    size_t cur_ = 0;

    const Token& peek() const { return toks_[cur_]; }
    const Token& at(size_t n) const {
        return cur_ + n < toks_.size() ? toks_[cur_ + n] : toks_.back();
    }
    Token advance() { return toks_[cur_++]; }
    bool check(Tok t) const { return peek().type == t; }
    void expect(Tok t, const char* what);
    [[noreturn]] void error(const std::string& msg);

    ValuePtr parseValue();
    Module parseModule();
};

}  // namespace spider::tm
