#include "tm/lexer.h"

namespace spider::tm {

static bool isIdentStart(char c) {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_';
}
static bool isIdentChar(char c) {
    return isIdentStart(c) || (c >= '0' && c <= '9') || c == '-';
}
static bool isDigit(char c) { return c >= '0' && c <= '9'; }

std::vector<Token> Lexer::scan() {
    std::vector<Token> out;
    while (!atEnd()) {
        char c = peek();

        // whitespace
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') { advance(); continue; }

        // comments
        if (c == '/' && peek2() == '/') {
            while (!atEnd() && peek() != '\n') advance();
            continue;
        }
        if (c == '/' && peek2() == '*') {
            advance(); advance();
            while (!atEnd() && !(peek() == '*' && peek2() == '/')) advance();
            if (!atEnd()) { advance(); advance(); }
            continue;
        }

        int sl = line_, sc = col_;
        if (isIdentStart(c)) {
            std::string text;
            while (!atEnd() && isIdentChar(peek())) text += advance();
            Tok t = Tok::IDENT;
            if (text == "module") t = Tok::MODULE;
            else if (text == "true") t = Tok::TRUE;
            else if (text == "false") t = Tok::FALSE;
            out.push_back({t, text, sl, sc});
            continue;
        }
        if (c == '"') {
            advance();
            std::string text;
            while (!atEnd() && peek() != '"') {
                if (peek() == '\\') { advance(); text += advance(); }
                else text += advance();
            }
            advance();  // closing quote
            out.push_back({Tok::STRING, text, sl, sc});
            continue;
        }
        if (isDigit(c)) {
            std::string text;
            while (!atEnd() && (isDigit(peek()) || peek() == '.')) text += advance();
            out.push_back({Tok::NUMBER, text, sl, sc});
            continue;
        }

        Tok t;
        char ch = advance();
        switch (ch) {
            case '{': t = Tok::LBRACE; break;
            case '}': t = Tok::RBRACE; break;
            case '[': t = Tok::LBRACK; break;
            case ']': t = Tok::RBRACK; break;
            case ':': t = Tok::COLON; break;
            case ',': t = Tok::COMMA; break;
            default: {
                // skip unknown single chars
                out.push_back({Tok::IDENT, std::string(1, ch), sl, sc});
                continue;
            }
        }
        out.push_back({t, std::string(1, ch), sl, sc});
    }
    out.push_back({Tok::EOF_TOK, "", line_, col_});
    return out;
}

}  // namespace spider::tm
