#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Florum – az Event Calendar plasmoid magyar fordítása (hu.po + .mo)
==================================================================

A widget (Event Calendar, Plasma 6) szövegei a saját `.po` fájljaiból
készülnek; magyar fordítás **nincs** hozzá (2026-10 állapot). Ez a szkript
a hivatalos sablonból (`template.pot`, 587 szöveg) és a `hu-1.py`–`hu-3.py`
fájlokban lévő fordításokból előállítja:

    hu.po                                                        (forrás)
    plasma_applet_org.kde.plasma.eventcalendar.mo                 (bináris)

Használat:
    python3 forditas/keszit.py                # hu.po + .mo elkészítése
    python3 forditas/keszit.py --ellenoriz    # csak ellenőrzés (lefedettség, %1)

A .mo telepítése: `bash kde-eventcalendar-magyar.sh`
"""

import argparse
import importlib.util
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "plasma_applet_org.kde.plasma.eventcalendar"
PO = os.path.join(HERE, "hu.po")
MO = os.path.join(HERE, DOMAIN + ".mo")


# ---------------------------------------------------------------- beolvasás
def load_entries():
    """A template.pot bejegyzései sorrendben: [{ctx, id, pl}]."""
    path = os.path.join(HERE, "entries.json")
    if os.path.exists(path):
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    # tartalék: a .pot értelmezése
    import re
    raw = io.open(os.path.join(HERE, "template.pot"), encoding="utf-8").read().split("\n")

    def unq(x):
        body = x.strip()[1:-1]
        out, i = [], 0
        while i < len(body):
            c = body[i]
            if c == "\\":
                n = body[i + 1]
                out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(n, n))
                i += 2
            else:
                out.append(c)
                i += 1
        return "".join(out)

    entries, cur = [], {"ctx": None, "id": None, "pl": None, "act": None}

    def finalize():
        if cur["id"]:
            entries.append({"ctx": cur["ctx"], "id": cur["id"], "pl": cur["pl"]})

    for ln in raw:
        if ln.startswith("msgctxt "):
            finalize()
            cur = {"ctx": unq(ln[8:]), "id": None, "pl": None, "act": "ctx"}
        elif ln.startswith("msgid_plural "):
            cur["pl"] = unq(ln[13:]); cur["act"] = "pl"
        elif ln.startswith("msgid "):
            if cur["id"] is not None:
                finalize()
                cur = {"ctx": None, "id": None, "pl": None, "act": "id"}
            cur["id"] = unq(ln[6:]); cur["act"] = "id"
        elif ln.startswith('"'):
            v = unq(ln)
            if cur["act"] == "id":
                cur["id"] = (cur["id"] or "") + v
            elif cur["act"] == "pl":
                cur["pl"] = (cur["pl"] or "") + v
            elif cur["act"] == "ctx":
                cur["ctx"] = (cur["ctx"] or "") + v
        elif ln.startswith("msgstr"):
            cur["act"] = "str"
    finalize()
    return [e for e in entries
            if e["id"] and "Content-Type" not in e["id"] and not e["id"].startswith("Project-Id")]


def load_hu():
    """A három fordítás-rész összefűzése (kulcs: sorszám)."""
    out = {}
    for name in ("hu-1.py", "hu-2.py", "hu-3.py"):
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        spec = importlib.util.spec_from_file_location(name[:-3].replace("-", "_"), path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for attr in dir(mod):
            if attr.startswith("HU"):
                out.update(getattr(mod, attr))
    return out


# ---------------------------------------------------------------- ellenőrzés
def tokens(text):
    """A formázó-jelölők halmaza (%1, %2, %u, …) – ezeknek meg kell maradniuk."""
    out, i = set(), 0
    while i < len(text) - 1:
        if text[i] == "%" and text[i + 1] in "0123456789usnd":
            j = i + 1
            while j < len(text) and text[j].isdigit():
                j += 1
            if j == i + 1:
                j += 1
            out.add(text[i:j])
            i = j
        else:
            i += 1
    return out


def validate(entries, hu):
    problems, missing = [], []
    for idx, e in enumerate(entries):
        tr = hu.get(idx)
        if tr is None or (isinstance(tr, str) and not tr.strip()):
            missing.append(idx)
            continue
        forms = tr if isinstance(tr, list) else [tr]
        if isinstance(tr, list) and len(tr) != 2:
            problems.append((idx, "a többes számhoz 2 alak kell"))
        # többes számnál a többes alak (msgid_plural) is hozhat jelölőt
        eredeti = tokens(e["id"]) | (tokens(e["pl"]) if e["pl"] else set())
        for n, f in enumerate(forms):
            if n == 0 and e["pl"] and not tokens(f):
                continue        # magyar egyes szám: „Szundi 1 percre” – jó így
            if not eredeti <= tokens(f):
                problems.append((idx, "hiányzó jelölő: %s → %s"
                                 % (", ".join(sorted(eredeti - tokens(f))), f[:60])))
            if tokens(f) and not eredeti:
                problems.append((idx, "a fordításban van %% jelölő, az eredetiben nincs: " + f[:60]))
    return problems, missing


# ---------------------------------------------------------------- .po kiírás
def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def build_po(entries, hu):
    out = [
        '# Event Calendar – magyar fordítás (Florum mellett)',
        '# A widget (plasma_applet_org.kde.plasma.eventcalendar) saját szövegeihez.',
        '# Készült a hivatalos template.pot alapján, kézi fordítással.',
        '#',
        'msgid ""',
        'msgstr ""',
        '"Project-Id-Version: eventcalendar (Florum magyarítás)\\n"',
        '"Report-Msgid-Bugs-To: https://github.com/divinae/plasma-applet-eventcalendar\\n"',
        '"PO-Revision-Date: 2026-10-23 12:00+0200\\n"',
        '"Last-Translator: Florum magyarítás\\n"',
        '"Language-Team: Hungarian\\n"',
        '"Language: hu\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"',
        '',
    ]
    for idx, e in enumerate(entries):
        tr = hu.get(idx)
        if tr is None:
            continue
        if e["ctx"]:
            out.append('msgctxt "%s"' % esc(e["ctx"]))
        out.append('msgid "%s"' % esc(e["id"]))
        if e["pl"]:
            out.append('msgid_plural "%s"' % esc(e["pl"]))
            forms = tr if isinstance(tr, list) else [tr, tr]
            out.append('msgstr[0] "%s"' % esc(forms[0]))
            out.append('msgstr[1] "%s"' % esc(forms[1]))
        else:
            out.append('msgstr "%s"' % esc(tr if isinstance(tr, str) else tr[0]))
        out.append('')
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- .mo kiírás
def build_mo(entries, hu):
    """GNU gettext .mo (little endian), plurális alakokkal."""
    catalog = {"": "Plural-Forms: nplurals=2; plural=(n != 1);\n"
                   "Content-Type: text/plain; charset=UTF-8\n"
                   "Language: hu\n"
                   "MIME-Version: 1.0\n"}
    for idx, e in enumerate(entries):
        tr = hu.get(idx)
        if tr is None:
            continue
        key = (e["ctx"] + "\x04" + e["id"]) if e["ctx"] else e["id"]
        if e["pl"]:
            forms = tr if isinstance(tr, list) else [tr, tr]
            # a .mo-ban a kulcs: "egyes\x00többes" (így keresi a gettext is)
            key = key + "\x00" + e["pl"]
            catalog[key] = "\x00".join(forms)
        else:
            catalog[key] = tr if isinstance(tr, str) else tr[0]

    keys = sorted(catalog)
    offsets, ids, strs = [], b"", b""
    for k in keys:
        kb = k.encode("utf-8")
        vb = catalog[k].encode("utf-8")
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b"\x00"
        strs += vb + b"\x00"

    n = len(keys)
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    out = struct.pack("<7I", 0x950412de, 0, n, 7 * 4, 7 * 4 + 8 * n, 0, 0)
    for o in offsets:
        out += struct.pack("<2I", o[1], keystart + o[0])
    for o in offsets:
        out += struct.pack("<2I", o[3], valuestart + o[2])
    out += ids + strs
    return out


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="Event Calendar – magyar fordítás készítése")
    ap.add_argument("--ellenoriz", action="store_true", help="csak ellenőrzés")
    args = ap.parse_args(argv)

    entries = load_entries()
    hu = load_hu()
    problems, missing = validate(entries, hu)

    kesz = len([1 for i in range(len(entries)) if hu.get(i)])
    print("Szövegek: %d · lefordítva: %d (%.0f%%)" % (len(entries), kesz, 100.0 * kesz / max(1, len(entries))))
    if missing:
        print("Hiányzó sorszámok: %s" % ", ".join(str(i) for i in missing[:20]))
    if problems:
        print("Problémák (%d):" % len(problems))
        for idx, msg in problems[:15]:
            print("  #%d  %s" % (idx, msg))
    if args.ellenoriz:
        return 1 if (missing or problems) else 0

    po = build_po(entries, hu)
    with io.open(PO, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(po)
    mo = build_mo(entries, hu)
    with open(MO, "wb") as fh:
        fh.write(mo)
    print("Elkészült: %s (%.1f kB)" % (os.path.basename(PO), len(po) / 1024))
    print("Elkészült: %s (%.1f kB, %d bejegyzés)"
          % (os.path.basename(MO), len(mo) / 1024, len(entries) - len(missing)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
