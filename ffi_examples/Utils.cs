// Utils.cs — SpiderLang FFI — C#
using System; using System.Collections.Generic; using System.Linq;
public class Utils {
    public static bool Verify(string s){ Console.WriteLine("C# verify: "+s); return !string.IsNullOrEmpty(s); }
    public static string Encrypt(string s){ return "enc("+s+")"; }
    public static int Checksum(byte[] data){ return data.Sum(b=> (int)b); }
    public static bool ValidateHeader(string m){ return m=="ANDROID!"; }
    public static bool PageAlign(int size,int page){ return size%page==0; }
    public static bool HeaderVersion(int v){ return v>=0&&v<=4; }
    public static bool ImageType(string t){ return new[]{"boot","recovery","vendor_boot"}.Contains(t); }
    public static string PartitionRole(string m){ var map=new Dictionary<string,string>{{"/system","system"}}; return map.ContainsKey(m)?map[m]:"data"; }
    public static bool ABCheck(string f){ return f.Contains("slotselect"); }
    public static int SizeToBytes(int n,int u){ return n*u; }
    public static List<Dictionary<string,string>> ParseFstab(string c){ return new List<Dictionary<string,string>>(); }
    public static List<string> LunchCombos(string c){ return c.Split('\n').Where(l=>l.Contains("add_lunch_combo")).ToList(); }
    public static bool BoardArch(string a){ return new[]{"arm64","arm"}.Contains(a); }
    public static int KernelOffset(int b){ return b+0x8000; }
}
