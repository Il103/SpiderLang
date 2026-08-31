// Logic.kt — SpiderLang FFI — Kotlin logic
fun verify(s: String): Boolean { println("Kotlin verify: $s"); return s.isNotEmpty() }
fun encrypt(s: String): String = "enc($s)"
fun checksum(data: ByteArray): Int = data.sumOf { it.toInt() }
fun validateHeader(magic: String): Boolean = magic == "ANDROID!"
fun pageAlign(size: Int, page: Int): Boolean = size % page == 0
fun headerVersion(v: Int): Boolean = v in 0..4
fun imageType(t: String): Boolean = t in listOf("boot","recovery","vendor_boot","init_boot")
fun partitionRole(mount: String): String = mapOf("/system" to "system","/vendor" to "vendor")[mount] ?: "data"
fun abCheck(flags: String): Boolean = "slotselect" in flags
fun sizeToBytes(n: Int, unit: Int): Int = n * unit
fun parseFstab(content: String): List<Map<String,String>> = emptyList()
fun lunchCombos(c: String): List<String> = c.lines().filter { "add_lunch_combo" in it }
fun boardArch(a: String): Boolean = a in listOf("arm64","arm","x86_64")
fun kernelOffset(base: Int): Int = base + 0x8000
fun ramdiskOffset(base: Int): Int = base + 0x01000000
fun toMB(b: Int): Int = b / (1024*1024)
fun fromMB(m: Int): Int = m * 1024 * 1024
