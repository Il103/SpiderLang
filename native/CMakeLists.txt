cmake_minimum_required(VERSION 3.15)
project(SpiderLangNative VERSION 3.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(spider
    src/main.cpp
    src/tm/lexer.cpp
    src/tm/parser.cpp
    src/tm/validate.cpp
    src/util/fs.cpp
    src/chip/chip.cpp
)

target_include_directories(spider PRIVATE src)
