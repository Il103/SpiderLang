# script.pl — SpiderLang FFI — Perl
sub verify { print "Perl verify: $_[0]\n"; return length($_[0])>0; }
sub encrypt { return "enc($_[0])"; }
sub checksum { my $sum=0; $sum+=$_ for @_; return $sum; }
sub validate_header { return $_[0] eq "ANDROID!"; }
sub page_align { return $_[0] % $_[1] == 0; }
sub header_version { return $_[0]>=0&&$_[0]<=4; }
sub image_type { return $_[0] eq "boot"||$_[0] eq "recovery"; }
sub partition_role { my %m=("/system"=>"system"); return $m{$_[0]}||"data"; }
sub ab_check { return index($_[0],"slotselect")!=-1; }
sub size_to_bytes { return $_[0]*$_[1]; }
sub lunch_combos { my @r; for(split /\n/, $_[0]){ push @r,$_ if /add_lunch_combo/ } return @r; }
sub board_arch { return $_[0] eq "arm64"; }
sub kernel_offset { return $_[0]+0x8000; }
1;
