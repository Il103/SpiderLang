<?php
// api.php — SpiderLang FFI — PHP
function verify($s){ echo "PHP verify: $s\n"; return !empty($s); }
function encrypt($s){ return "enc($s)"; }
function checksum($data){ return array_sum($data); }
function validateHeader($m){ return $m==="ANDROID!"; }
function pageAlign($size,$page){ return $size % $page === 0; }
function headerVersion($v){ return $v>=0 && $v<=4; }
function imageType($t){ return in_array($t,["boot","recovery","vendor_boot"]); }
function partitionRole($m){ $map=["/system"=>"system"]; return $map[$m] ?? "data"; }
function abCheck($f){ return strpos($f,"slotselect")!==false; }
function sizeToBytes($n,$u){ return $n*$u; }
function parseFstab($c){ return []; }
function lunchCombos($c){ $r=[]; foreach(explode("\n",$c) as $l) if(strpos($l,"add_lunch_combo")!==false) $r[]=$l; return $r; }
function boardArch($a){ return in_array($a,["arm64","arm"]); }
function kernelOffset($b){ return $b+0x8000; }
