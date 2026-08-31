// ui.dart — SpiderLang FFI — Dart
bool verify(String s){ print("Dart verify: $s"); return s.isNotEmpty; }
String encrypt(String s)=> "enc($s)";
int checksum(List<int> data)=> data.fold(0,(a,b)=>a+b);
bool validateHeader(String m)=> m=="ANDROID!";
bool pageAlign(int size,int page)=> size%page==0;
bool headerVersion(int v)=> v>=0&&v<=4;
bool imageType(String t)=> ["boot","recovery","vendor_boot"].contains(t);
String partitionRole(String m)=> {"/system":"system","/vendor":"vendor"}[m]??"data";
bool abCheck(String f)=> f.contains("slotselect");
int sizeToBytes(int n,int u)=> n*u;
List<Map<String,String>> parseFstab(String c)=> [];
List<String> lunchCombos(String c)=> c.split("\n").where((l)=>l.contains("add_lunch_combo")).toList();
bool boardArch(String a)=> ["arm64","arm"].contains(a);
int kernelOffset(int b)=> b+0x8000;
