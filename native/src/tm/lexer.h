// Android.tm scanner. Turns Android.tm source text into a token stream.
#pragma once
#include <string>
#include <vector>

namespace spider::tm {

enum class Tok {
    MODULE,            // module
    IDENT,             // foo, cc_binary, arch
    STRING,            // "android-30"
    NUMBER,            // 29
    LBRACE, RBRACE,    // { }
    LBRACK, RBRACK,    // [ ]
    COLON, COMMA,      // : ,
    TRUE, FALSE,       // true false
    EOF_TOK
};

struct Token {
    Tok type;
    std::string text;
    int line, col;
};

class Lexer {
public:
    explicit Lexer(const std::string& src) : src_(src) {}
    std::vector<Token> scan();

private:
    const std::string& src_;
    size_t pos_ = 0;
    int line_ = 1, col_ = 1;

    bool atEnd() const { return pos_ >= src_.size(); }
    char peek() const { return atEnd() ? '\0' : src_[pos_]; }
    char peek2() const { return pos_ + 1 >= src_.size() ? '\0' : src_[pos_ + 1]; }
    char advance() {
        char c = src_[pos_++];
        if (c == '\n') { line_++; col_ = 1; } else { col_++; }
        return c;
    }
};

}  // namespace spider::tm
