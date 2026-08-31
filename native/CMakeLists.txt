cmake_minimum_required(VERSION 3.15)
project(SpiderLangNative VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(spider
    src/main.cpp
    src/lexer.cpp
    # src/parser.cpp  (next milestone)
    # src/interpreter.cpp
)

target_include_directories(spider PRIVATE src)

# Spider ASCII build
add_custom_target(spider_ascii ALL
    COMMAND ${CMAKE_COMMAND} -E echo "🕷️ SpiderLang Native Build Complete"
)
