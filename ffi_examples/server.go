// server.go — SpiderLang FFI — Go server helper
package main
import (
    "fmt"
    "strings"
    "strconv"
)
func Verify(s string) bool { fmt.Println("Go verify:", s); return len(s) > 0 }
func Serve(port int) { fmt.Printf("Go serve on %d\n", port) }
func Checksum(data []byte) int { sum := 0; for _, b := range data { sum += int(b) }; return sum }
func ValidateHeader(magic string) bool { return magic == "ANDROID!" }
func PageAlign(size, page int) bool { return size%page == 0 }
func HeaderVersion(v int) bool { return v >= 0 && v <= 4 }
func ImageType(t string) bool { return t=="boot"||t=="recovery"||t=="vendor_boot" }
func PartitionRole(mount string) string { m:= map[string]string{"/system":"system","/vendor":"vendor","/boot":"boot"}; if r,ok:=m[mount]; ok {return r}; return "data" }
func ABCheck(flags string) bool { return strings.Contains(flags, "slotselect") }
func SizeToBytes(n int, unit int) int { return n*unit }
func ParseFstab(content string) []map[string]string { return nil }
func LunchCombos(c string) []string { var r []string; for _,l:=range strings.Split(c,"\n"){ if strings.Contains(l,"add_lunch_combo"){r=append(r,l)}}; return r }
func BoardArch(a string) bool { return a=="arm64"||a=="arm" }
func KernelOffset(base int) int { return base + 0x8000 }
func ToMB(b int) int { return b/(1024*1024) }
func FromMB(m int) int { return m*1024*1024 }
