// SpiderLang Native C++ — Lexer (Handmade, no flex)
// From-scratch char-by-char scanner, produces Tokens for Parser
// This is the native port — Python prototype is bootstrap only.
// Build: cmake -B build && cmake --build build
#pragma once
#include <string>
#include <vector>

enum class TokenType {
    LPAREN, RPAREN, LBRACE, RBRACE, LBRACK, RBRACK,
    COMMA, DOT, COLON, SEMICOLON,
    PLUS, MINUS, STAR, SLASH, PERCENT,
    EQ, EQEQ, NEQ, LT, GT, LTE, GTE, BANG, AND, OR, ARROW,
    IDENTIFIER, NUMBER, STRING,
    LET, FUNC, IF, ELSE, RETURN, PRINT, USE, AS, BOARD, TRUE, FALSE, NUL,
    EOF_TOKEN
};

struct Token {
    TokenType type;
    std::string lexeme;
    int line, col;
};

class Lexer {
    std::string source;
    std::string filename;
    size_t start = 0, current = 0;
    int line = 1, col = 1, start_col = 1;
    std::vector<Token> tokens;
public:
    Lexer(const std::string& src, const std::string& file="<input>") : source(src), filename(file) {}
    std::vector<Token> scan();
private:
    bool isAtEnd();
    char advance();
    char peek();
    char peekNext();
    bool match(char c);
    void addToken(TokenType t);
    void scanToken();
    void scanString(char quote);
    void scanNumber();
    void scanIdentifier();
};
