-- config.lua — SpiderLang FFI — Lua
function verify(s) print("Lua verify: "..s) return s~="" end
function encrypt(s) return "enc("..s..")" end
function checksum(data) local sum=0; for _,b in ipairs(data) do sum=sum+b end; return sum end
function validate_header(m) return m=="ANDROID!" end
function page_align(size,page) return size % page == 0 end
function header_version(v) return v>=0 and v<=4 end
function image_type(t) return t=="boot" or t=="recovery" or t=="vendor_boot" end
function partition_role(m) local map={["/system"]="system"}; return map[m] or "data" end
function ab_check(f) return string.find(f,"slotselect")~=nil end
function size_to_bytes(n,u) return n*u end
function parse_fstab(c) return {} end
function lunch_combos(c) local r={}; for l in string.gmatch(c,"[^\n]+") do if string.find(l,"add_lunch_combo") then table.insert(r,l) end end; return r end
function board_arch(a) return a=="arm64" or a=="arm" end
function kernel_offset(b) return b+0x8000 end
