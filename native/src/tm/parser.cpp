#include "tm/parser.h"

namespace spider::tm {

void Parser::error(const std::string& msg) {
    throw ParseError{msg, peek().line, peek().col};
}

void Parser::expect(Tok t, const char* what) {
    if (!check(t)) error(std::string("expected ") + what);
    advance();
}

ValuePtr Parser::parseValue() {
    auto v = std::make_shared<Value>();
    if (check(Tok::STRING)) { v->kind = Value::Kind::Str; v->str_ = advance().text; }
    else if (check(Tok::NUMBER)) { v->kind = Value::Kind::Num; v->num_ = std::stod(advance().text); }
    else if (check(Tok::TRUE) || check(Tok::FALSE)) { v->kind = Value::Kind::Bool; v->bool_ = (advance().type == Tok::TRUE); }
    else if (check(Tok::LBRACK)) {
        v->kind = Value::Kind::List;
        advance();
        while (!check(Tok::RBRACK)) {
            if (check(Tok::EOF_TOK)) error("unterminated list");
            v->list_.push_back(parseValue());
            if (check(Tok::COMMA)) advance();
        }
        advance();
    }
    else if (check(Tok::LBRACE)) {
        v->kind = Value::Kind::Block;
        advance();
        while (!check(Tok::RBRACE)) {
            if (check(Tok::EOF_TOK)) error("unterminated block");
            if (!check(Tok::IDENT)) error("expected property name in block");
            std::string name = advance().text;
            expect(Tok::COLON, "':' after property name");
            v->block_.emplace_back(name, parseValue());
            if (check(Tok::COMMA)) advance();
        }
        advance();
    }
    else {
        error("expected a value (string, number, bool, list or block)");
    }
    return v;
}

Module Parser::parseModule() {
    Module m;
    m.line = peek().line;
    m.col = peek().col;
    // optional module name
    if (check(Tok::STRING)) m.name = advance().text;
    else if (check(Tok::IDENT) && at(1).type != Tok::LBRACE) m.name = advance().text;
    // optional type keyword (module "x" type "cc_binary" { ... })
    if (check(Tok::IDENT) && peek().text == "type") {
        advance();
        if (!check(Tok::STRING)) error("expected string after 'type'");
        m.type = advance().text;
    }
    expect(Tok::LBRACE, "'{' to open module");
    while (!check(Tok::RBRACE)) {
        if (check(Tok::EOF_TOK)) error("unterminated module");
        if (!check(Tok::IDENT)) error("expected property name");
        std::string name = advance().text;
        expect(Tok::COLON, "':' after property name");
        ValuePtr v = parseValue();
        if (check(Tok::COMMA)) advance();
        m.props.emplace_back(name, v);
        m.byName[name] = v;
    }
    advance();  // }
    return m;
}

File Parser::parse() {
    File file;
    while (!check(Tok::EOF_TOK)) {
        if (check(Tok::MODULE) || (check(Tok::IDENT) && at(1).type == Tok::LBRACE)) {
            advance();
            file.modules.push_back(parseModule());
        } else {
            error("expected 'module' at top level");
        }
    }
    return file;
}

}  // namespace spider::tm
