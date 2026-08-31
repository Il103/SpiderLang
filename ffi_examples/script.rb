# script.rb — SpiderLang FFI — Ruby
def verify(s); puts "Ruby verify: #{s}"; !s.empty?; end
def encrypt(s); "enc(#{s})"; end
def checksum(data); data.sum; end
def validate_header(m); m == "ANDROID!"; end
def page_align(size, page); size % page == 0; end
def header_version(v); v.between?(0,4); end
def image_type(t); %w[boot recovery vendor_boot].include?(t); end
def partition_role(m); {"/system"=>"system","/vendor"=>"vendor"}[m] || "data"; end
def ab_check(f); f.include?("slotselect"); end
def size_to_bytes(n,u); n*u; end
def parse_fstab(c); []; end
def lunch_combos(c); c.lines.select{|l| l.include?("add_lunch_combo")}; end
def board_arch(a); %w[arm64 arm].include?(a); end
def kernel_offset(b); b + 0x8000; end
def to_mb(b); b/(1024*1024); end
