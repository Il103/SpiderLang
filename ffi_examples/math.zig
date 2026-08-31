// math.zig — SpiderLang FFI — Zig
const std = @import("std");
pub fn verify(s: []const u8) bool { return s.len > 0; }
pub fn encrypt(s: []const u8) []const u8 { return s; }
pub fn checksum(data: []const u8) u32 { var sum: u32 = 0; for (data) |b| sum += b; return sum; }
pub fn validateHeader(magic: []const u8) bool { return std.mem.eql(u8, magic, "ANDROID!"); }
pub fn pageAlign(size: usize, page: usize) bool { return size % page == 0; }
pub fn headerVersion(v: u32) bool { return v <= 4; }
pub fn imageType(t: []const u8) bool { return std.mem.eql(u8, t, "boot"); }
pub fn partitionRole(mount: []const u8) []const u8 { return "data"; }
pub fn abCheck(flags: []const u8) bool { return std.mem.indexOf(u8, flags, "slotselect") != null; }
pub fn sizeToBytes(n: usize, unit: usize) usize { return n * unit; }
pub fn kernelOffset(base: usize) usize { return base + 0x8000; }
