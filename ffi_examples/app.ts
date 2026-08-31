// app.ts — SpiderLang FFI — TypeScript
export function verify(s: string): boolean { console.log("TS verify:", s); return s.length>0; }
export function encrypt(s: string): string { return `enc(${s})`; }
export function checksum(data: number[]): number { return data.reduce((a,b)=>a+b,0); }
export function validateHeader(magic: string): boolean { return magic==="ANDROID!"; }
export function pageAlign(size: number, page: number): boolean { return size%page===0; }
export function headerVersion(v: number): boolean { return v>=0&&v<=4; }
export function imageType(t: string): boolean { return ["boot","recovery","vendor_boot"].includes(t); }
export function partitionRole(mount: string): string { const m:any={"/system":"system"}; return m[mount]??"data"; }
export function abCheck(flags: string): boolean { return flags.includes("slotselect"); }
export function sizeToBytes(n: number, u: number): number { return n*u; }
export function lunchCombos(c: string): string[] { return c.split("\n").filter(l=>l.includes("add_lunch_combo")); }
export function boardArch(a: string): boolean { return ["arm64","arm"].includes(a); }
export function kernelOffset(b: number): number { return b+0x8000; }
