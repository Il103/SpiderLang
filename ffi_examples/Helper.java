// Helper.java — SpiderLang FFI — Java helper
import java.util.*;
public class Helper {
    public static boolean verify(String s){ System.out.println("Java verify: "+s); return s!=null&&!s.isEmpty(); }
    public static String encrypt(String s){ return "enc("+s+")"; }
    public static int checksum(byte[] data){ int sum=0; for(byte b:data) sum+=b; return sum; }
    public static boolean validateHeader(String m){ return "ANDROID!".equals(m); }
    public static boolean pageAlign(int size,int page){ return size%page==0; }
    public static boolean headerVersion(int v){ return v>=0&&v<=4; }
    public static boolean imageType(String t){ return Arrays.asList("boot","recovery","vendor_boot").contains(t); }
    public static String partitionRole(String m){ Map<String,String> map=new HashMap<>(); map.put("/system","system"); return map.getOrDefault(m,"data"); }
    public static boolean abCheck(String f){ return f.contains("slotselect"); }
    public static int sizeToBytes(int n,int u){ return n*u; }
    public static List<Map<String,String>> parseFstab(String c){ return new ArrayList<>(); }
    public static List<String> lunchCombos(String c){ List<String> r=new ArrayList<>(); for(String l:c.split("\n")) if(l.contains("add_lunch_combo")) r.add(l); return r; }
    public static boolean boardArch(String a){ return a.equals("arm64")||a.equals("arm"); }
    public static int kernelOffset(int b){ return b+0x8000; }
}
