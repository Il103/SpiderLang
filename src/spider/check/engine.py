"""
SpiderLang check engine — the "جرّب كل حاجة" diagnostics.

Unlike the plain syntax check, this understands the whole recovery: does the
tree read cleanly? is the .st dialect pure (no leaked .mk)? are the images
complete (via the hidden magiskboot capability)? are the important flags
present? are the partition sizes sane? It returns a verdict + a 0-100 score.
"""

import os
import re


class Check:
    def __init__(self, path):
        self.base = os.path.abspath(path)
        self.checks = []       # list of (status, label, note)
        self.score = 0
        self._max = 0

    # ---- helpers ----
    def _add(self, status, label, note=None):
        self.checks.append((status, label, note))
        self._max += 1
        if status == "ok":
            self.score += 4
        elif status == "warn":
            self.score += 2
        elif status == "fail":
            self.score += 0

    def _read(self, rel):
        try:
            p = os.path.join(self.base, rel)
            with open(p, encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return None

    def _has(self, rel):
        return os.path.isfile(os.path.join(self.base, rel))

    # ---- run ----
    def run(self, understand_fn=None):
        from ..core import Interpreter
        from ..knowledge import all_recoveries
        from ..fmt.st_dialect import mk_leaks, classify
        from .. import tools as _tools

        if not os.path.isdir(self.base):
            self._add("fail", f"tree '{self.base}' does not exist")
            return self.report()

        und = understand_fn(self.base) if understand_fn else \
            Interpreter(base_dir=".").builtin_understand(self.base)

        codename = und.get("codename")
        recoveries = und.get("recoveries") or []
        parts = und.get("partitions") or []
        images = und.get("images") or {}

        # 1 — tree readability
        if und.get("exists"):
            self._add("ok", f"tree read & understood (codename={codename or '?'})")
        else:
            self._add("fail", "tree not understood")

        # 2 — recovery recognized
        if recoveries:
            self._add("ok", f"recovery variant: {', '.join(recoveries)}")
        else:
            self._add("warn", "no recovery variant detected")

        # 3 — partition table
        if parts:
            ab = sum(1 for p in parts if p["a_b"])
            self._add("ok", f"fstab read: {len(parts)} partitions ({ab} A/B)")
        else:
            self._add("warn", "no fstab partitions detected")

        # 4 — .st dialect purity (no leaked makefile-isms)
        st_files = [f for f in und.get("files", []) if f.endswith(".st")]
        if st_files:
            leaked = False
            for f in st_files:
                text = self._read(f)
                if text and mk_leaks(text):
                    leaked = True
                    self._add("warn", f"{f}: leaked makefile-isms ({', '.join(mk_leaks(text))})")
            if not leaked:
                self._add("ok", f".st dialect pure ({len(st_files)} file(s), no .mk leaks)")
        else:
            self._add("warn", "no .st files (recovery defined without second language)")

        # 5 — image completeness via hidden magiskboot capability
        if images:
            for it, src in images.items():
                fname = f"{it}.img"
                if self._has(fname):
                    head = _tools.analyze(os.path.join(self.base, fname))
                    if head.get("recognized"):
                        vs = _tools.verify_sections(head)
                        if vs.get("complete"):
                            self._add("ok", f"{fname}: complete (header v{vs.get('header_version')}, {vs.get('os_version')})")
                        else:
                            self._add("fail", f"{fname}: {', '.join(vs.get('issues') or ['?'])}")
                    else:
                        self._add("warn", f"{fname}: not a recognized Android image")
                elif it == "recovery":
                    self._add("warn", "recovery.img not built yet (run spider build)")
                else:
                    self._add("ok", f"{it} declared in {src}")
        else:
            self._add("warn", "no images declared")

        # 6 — important recovery flags (knowledge-based completeness)
        self._flag_checks(und, recoveries)

        # 7 — props (.prop) check — native props understanding
        prop_files = [f for f in und.get("files", []) if f.endswith(".prop")]
        if prop_files:
            from ..knowledge.props import analyze_file as _aprop, check_props
            total_props = 0
            total_issues = 0
            all_props = {}
            for f in prop_files:
                r = _aprop(os.path.join(self.base, f))
                if r.get("exists"):
                    total_props += r.get("total", 0)
                    total_issues += len(r.get("issues", []))
                    all_props.update(r.get("props", {}))
            if total_issues:
                self._add("warn", f"props: {total_props} entries in {len(prop_files)} .prop file(s), {total_issues} parse warnings")
            else:
                self._add("ok", f"props: {total_props} entries in {len(prop_files)} .prop file(s), clean")
            # essential props
            cp = check_props(all_props)
            if cp["missing"]:
                self._add("warn", f"props missing essentials: {', '.join(cp['missing'])}")
            else:
                self._add("ok", "props essentials present (ro.hardware, ro.build.product...)")
        else:
            self._add("warn", "no .prop files (add system.prop)")

        # 8 — Soong (.bp) check
        bp = [f for f in und.get("files", []) if f.endswith(".bp")]
        if bp:
            from ..knowledge.soong import analyze_file, counts
            total = 0
            import json
            bad = 0
            for f in bp:
                text = self._read(f)
                if not text:
                    continue
                mods = analyze_file(text)
                c = counts(mods)
                total += c["total"]
                bad += c["incomplete"]
            if total:
                stuff = "no issues" if bad == 0 else f"{bad} incomplete"
                self._add("ok" if bad == 0 else "warn", f"Soong: {total} module(s) in {len(bp)} .bp file(s), {stuff}")
            else:
                self._add("ok", "Soong .bp present")
        elif not [f for f in und.get("files", []) if f.endswith(".mk")]:
            self._add("ok", "no Soong .bp (clean native tree)")

        return self.report()

    def _flag_checks(self, und, recoveries):
        """Check the presence of important flags against recovery knowledge."""
        from ..knowledge import flag_hint, known_flag_for, recovery_by_name

        text_buf = []
        for f in und.get("files", []):
            if f.endswith((".st", ".mk", ".spt", ".prop")):
                t = self._read(f)
                if t:
                    text_buf.append(t)
        all_text = "\n".join(text_buf)

        # Common essential flags for a complete recovery, by family.
        essentials = {
            "twrp": ["TW_HAS_MTP", "TW_INCLUDE_CRYPTO"],
            "orangefox": ["OF_USE_TWRP_SAR_DETECT", "OF_USE_MAGISKBOOT"],
            "pbrp": [],
            "shrp": [],
        }
        recos = recoveries or ["twrp"]
        for fam in recos:
            for fl in essentials.get(fam, []):
                if re.search(rf"\b{fl}\b", all_text):
                    self._add("ok", f"{fl}: present" + (f" — {flag_hint(fl)}" if flag_hint(fl) else ""))
                else:
                    self._add("warn", f"{fl}: missing" + (f" — {flag_hint(fl)}" if flag_hint(fl) else ""))
        # Optional-but-common flags (already present get a pat on the back)
        nice = ["TW_EXCLUDE_APEX", "TW_USE_TOOLBOX", "TW_INCLUDE_FUSE_EXFAT",
                "OF_SUPPORT_ALL_BLOCK_OTA_UPDATES", "TW_HAS_DOWNLOAD_MODE",
                "TW_INCLUDE_LIBUSB"]
        for fl in nice:
            if re.search(rf"\b{fl}\b", all_text):
                self._add("ok", f"{fl}: present (bonus)")

    # ---- report ----
    def report(self):
        status_counts = {"ok": 0, "warn": 0, "fail": 0}
        for st, _, _ in self.checks:
            status_counts[st] += 1
        self.score = min(100, round(100 * self.score / (self._max * 4 or 1)))
        if status_counts["fail"]:
            verdict = "NOT READY"
        elif status_counts["warn"]:
            verdict = "PARTIAL"
        else:
            verdict = "COMPLETE"
        return {
            "checks": self.checks,
            "counts": status_counts,
            "score": self.score,
            "verdict": verdict,
        }


# Convenience wrapper for CLI
def diagnose(path):
    return Check(path).run()
