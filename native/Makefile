# SpiderLang native chip — plain g++ make (no cmake required)
CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Isrc
SRC      := $(wildcard src/main.cpp src/tm/*.cpp src/util/*.cpp src/chip/*.cpp)
OBJ      := $(SRC:src/%.cpp=build/%.o)
BIN      := build/spider

all: $(BIN)

$(BIN): $(OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $@

build/%.o: src/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -rf build

.PHONY: all clean
