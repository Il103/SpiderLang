# analysis.R — SpiderLang FFI — R
verify <- function(s){ cat("R verify:", s, "\n"); nchar(s)>0 }
encrypt <- function(s){ paste0("enc(",s,")") }
checksum <- function(data){ sum(data) }
validate_header <- function(m){ m=="ANDROID!" }
page_align <- function(size,page){ size %% page == 0 }
header_version <- function(v){ v>=0 && v<=4 }
image_type <- function(t){ t %in% c("boot","recovery","vendor_boot") }
partition_role <- function(m){ map <- list("/system"="system"); if(m %in% names(map)) map[[m]] else "data" }
ab_check <- function(f){ grepl("slotselect",f) }
size_to_bytes <- function(n,u){ n*u }
lunch_combos <- function(c){ Filter(function(l) grepl("add_lunch_combo",l), strsplit(c,"\n")[[1]]) }
board_arch <- function(a){ a %in% c("arm64","arm") }
kernel_offset <- function(b){ b+0x8000 }
