// SpiderLang Native C++ Lexer — Handmade from scratch
// No external dependencies, pure char-by-char.
#include "lexer.h"
#include <cctype>
#include <unordered_map>
#include <stdexcept>

static std::unordered_map<std::string, TokenType> keywords = {
    {"let", TokenType::LET}, {"func", TokenType::FUNC},
    {"if", TokenType::IF}, {"else", TokenType::ELSE},
    {"return", TokenType::RETURN}, {"print", TokenType::PRINT},
    {"use", TokenType::USE}, {"as", TokenType::AS},
    {"board", TokenType::BOARD},
    {"true", TokenType::TRUE}, {"false", TokenType::FALSE},
    {"null", TokenType::NUL}
};

std::vector<Token> Lexer::scan() {
    while (!isAtEnd()) {
        start = current;
        start_col = col;
        scanToken();
    }
    tokens.push_back({TokenType::EOF_TOKEN, "", line, col});
    return tokens;
}

bool Lexer::isAtEnd() { return current >= source.size(); }
char Lexer::advance() {
    char c = source[current++];
    if (c == '\n') { line++; col = 1; } else col++;
    return c;
}
char Lexer::peek() { return isAtEnd() ? '\0' : source[current]; }
char Lexer::peekNext() { return current+1 >= source.size() ? '\0' : source[current+1]; }
bool Lexer::match(char e) { if (isAtEnd() || source[current]!=e) return false; current++; col++; return true; }
void Lexer::addToken(TokenType t) { tokens.push_back({t, source.substr(start, current-start), line, start_col}); }

void Lexer::scanToken() {
    char c = advance();
    switch(c) {
        case '(': addToken(TokenType::LPAREN); break;
        case ')': addToken(TokenType::RPAREN); break;
        case '{': addToken(TokenType::LBRACE); break;
        case '}': addToken(TokenType::RBRACE); break;
        case '[': addToken(TokenType::LBRACK); break;
        case ']': addToken(TokenType::RBRACK); break;
        case ',': addToken(TokenType::COMMA); break;
        case ':': addToken(TokenType::COLON); break;
        case ';': addToken(TokenType::SEMICOLON); break;
        case '.': addToken(TokenType::DOT); break;
        case '+': addToken(TokenType::PLUS); break;
        case '-': addToken(TokenType::MINUS); break;
        case '*': addToken(TokenType::STAR); break;
        case '%': addToken(TokenType::PERCENT); break;
        case '/':
            if (match('/')) { while(peek()!='\n' && !isAtEnd()) advance(); }
            else if (match('*')) { while(!(peek()=='*' && peekNext()=='/') && !isAtEnd()) advance(); if(!isAtEnd()){advance(); advance();} }
            else addToken(TokenType::SLASH);
            break;
        case '!': addToken(match('=')?TokenType::NEQ:TokenType::BANG); break;
        case '=': if(match('=')) addToken(TokenType::EQEQ); else if(match('>')) addToken(TokenType::ARROW); else addToken(TokenType::EQ); break;
        case '<': addToken(match('=')?TokenType::LTE:TokenType::LT); break;
        case '>': addToken(match('=')?TokenType::GTE:TokenType::GT); break;
        case '&': if(match('&')) addToken(TokenType::AND); break;
        case '|': if(match('|')) addToken(TokenType::OR); break;
        case '"': scanString('"'); break;
        case '\'': scanString('\''); break;
        case ' ': case '\r': case '\t': case '\n': break;
        default:
            if (isdigit(c)) scanNumber();
            else if (isalpha(c) || c=='_') scanIdentifier();
            else throw std::runtime_error("Unexpected char");
    }
}
void Lexer::scanString(char q) {
    std::string val;
    while(peek()!=q && !isAtEnd()) {
        if(peek()=='\\'){ advance(); char e=advance(); if(e=='n') val+='\n'; else if(e=='t') val+='\t'; else val+=e; }
        else val+=advance();
    }
    if(isAtEnd()) throw std::runtime_error("Unterminated string");
    advance();
    tokens.push_back({TokenType::STRING, source.substr(start, current-start), line, start_col});
}
void Lexer::scanNumber() {
    while(isdigit(peek())) advance();
    if(peek()=='.' && isdigit(peekNext())){ advance(); while(isdigit(peek())) advance(); }
    tokens.push_back({TokenType::NUMBER, source.substr(start, current-start), line, start_col});
}
void Lexer::scanIdentifier() {
    while(isalnum(peek()) || peek()=='_') advance();
    std::string txt = source.substr(start, current-start);
    auto it = keywords.find(txt);
    tokens.push_back({it!=keywords.end()?it->second:TokenType::IDENTIFIER, txt, line, start_col});
}
