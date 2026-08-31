// SpiderLang Native — filesystem & string helpers (no external deps)
#pragma once
#include <string>
#include <vector>

namespace spider::fs {

// Read a whole file. Returns false (and leaves out empty) on failure.
bool readFile(const std::string& path, std::string& out);

// Does the path exist?
bool exists(const std::string& path);

// Split a string on a delimiter.
std::vector<std::string> split(const std::string& s, char delim);

// Trim whitespace from both ends.
std::string trim(const std::string& s);

// Lowercase a string.
std::string lower(std::string s);

}  // namespace spider::fs
