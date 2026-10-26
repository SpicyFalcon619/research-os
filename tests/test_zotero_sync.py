#!/usr/bin/env python3
"""Offline tests for scripts/zotero_sync.py. Standard library only.

Run from the workspace root:  python tests/test_zotero_sync.py
Uses mocked Zotero API responses and temporary folders. It never contacts Zotero
(except to confirm that a closed local port is handled safely) and never touches
your real workspace files. Exits with status 1 if any check fails.
"""

import contextlib
import copy
import datetime
import hashlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import zotero_sync as zs  # noqa: E402

RESULTS = []


def check(name, cond, info=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{info}]" if (info and not cond) else ""))


def aborts(fn, contains=None, exc=zs.SyncAbort):
    try:
        fn()
    except exc as err:
        return contains is None or contains.lower() in str(err).lower()
    except Exception:
        return False
    return False


# ---------- mock helpers
def col(k, n, parent=None):
    return {"key": k, "version": 1, "library": {"type": "user"},
            "data": {"key": k, "name": n, "parentCollection": parent or False}, "meta": {}}


def item(k, cols, title="Paper", typ="conferencePaper", lib="user", **extra):
    d = {"key": k, "itemType": typ, "title": title, "collections": list(cols),
         "creators": [{"creatorType": "author", "firstName": "A", "lastName": "Smith"}],
         "date": "2020", "version": 1, "DOI": "10.1/x"}
    d.update(extra)
    return {"key": k, "version": 1,
            "library": {"type": lib, "id": 99999, "links": {"alternate": {"href": "https://www.zotero.org/users/12345/"}}},
            "links": {}, "meta": {"parsedDate": "2020"}, "data": d}


def att(k, parent, path=None, ct="application/pdf", mode="imported_url", fname="paper.pdf"):
    links = {"enclosure": {"href": Path(path).resolve().as_uri(), "type": ct}} if path else {}
    return {"key": k, "version": 1, "library": {"type": "user"}, "links": links, "meta": {},
            "data": {"key": k, "itemType": "attachment", "parentItem": parent, "contentType": ct,
                     "linkMode": mode, "filename": fname, "md5": "abc", "mtime": 1}}


def COLS():
    return [col("AAAAAAA1", "00 Inbox"), col("AAAAAAA2", "01 Foundations"), col("OTHER001", "Misc"),
            col("DENYROOT", "Excluded"), col("DENYCHL1", "Child One", "DENYROOT"), col("DENYGRC1", "Grand", "DENYCHL1")]


class Fake:
    """Stands in for ApiClient. `mode` injects incomplete-response failures."""

    def __init__(self, collections, items, trash=(), groups=0, coll_items=None, mode=None):
        self.collections, self.items, self.trash, self.groups = collections, items, list(trash), groups
        self.coll_items, self.mode, self.calls, self.paths = coll_items, mode, 0, []

    def get(self, path):
        self.paths.append(path)
        pth, _, q = path.partition("?")
        params = dict(p.split("=") for p in q.split("&") if "=" in p)
        limit, start = int(params.get("limit", 100)), int(params.get("start", 0))
        if pth == "/users/0/collections":
            data = self.collections
        elif pth == "/users/0/items":
            data = self.items
        elif pth == "/users/0/items/trash":
            data = self.trash
        elif pth == "/users/0/groups":
            return [], self.groups
        elif pth.startswith("/users/0/collections/") and pth.endswith("/items/top"):
            k = pth.split("/")[4]
            data = self.coll_items(k) if self.coll_items else [
                i for i in self.items if k in (i["data"].get("collections") or []) and not i["data"].get("parentItem")]
        else:
            raise AssertionError("unexpected path " + path)
        self.calls += 1
        total = len(data)
        if self.mode == "short" and pth == "/users/0/items":
            total += 2
        if self.mode == "drift" and pth == "/users/0/items":
            total += self.calls
        if self.mode == "nototal" and pth == "/users/0/items":
            total = None
        return data[start:start + limit], total


class Env:
    def __init__(self, tmp, page_size=100):
        self.tmp = Path(tmp)
        self.root, self.storage = self.tmp / "ws", self.tmp / "Zotero" / "storage"
        (self.root / "papers").mkdir(parents=True)
        (self.root / "refs").mkdir()
        self.storage.mkdir(parents=True)
        self.cfg = dict(api_base="http://127.0.0.1:23119/api", zotero_storage_dir=str(self.storage),
                        dest_dir="papers/zotero", manifest="refs/zotero-sync/manifest.jsonl",
                        reports_dir="refs/zotero-sync/reports", duplicate_scan_dirs=["papers"],
                        deny_root_name="Excluded", page_size=page_size,
                        allow=[{"key": "AAAAAAA1", "name": "00 Inbox"}, {"key": "AAAAAAA2", "name": "01 Foundations"}],
                        deny=[{"key": "DENYROOT", "name": "Excluded"}, {"key": "DENYCHL1", "name": "Child One"}])
        self.settings = zs.Settings(self.cfg, self.root)

    def pdf(self, attkey, name="paper.pdf", body=b"x"):
        d = self.storage / attkey
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        p.write_bytes(b"%PDF-1.4\n" + body)
        return p

    def snapshot(self):
        return sorted((str(p.relative_to(self.tmp)), p.stat().st_size, p.stat().st_mtime_ns)
                      for p in self.tmp.rglob("*") if p.is_file())

    def sha(self, p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def basic(env, extra_items=(), **kw):
    p = env.pdf("ATTOK001", body=b"eligible-one")
    items = [item("PARENT01", ["AAAAAAA2"], title="Eligible Paper"), att("ATTOK001", "PARENT01", p)] + list(extra_items)
    return Fake(COLS(), items, **kw), p


tmp = tempfile.mkdtemp()
counter = [0]


def fresh(**kw):
    counter[0] += 1
    return Env(Path(tmp) / f"e{counter[0]}", **kw)


try:
    # T1 denied parent + descendants (incl. an unconfigured grandchild) excluded; titles never leak
    e = fresh()
    denied = [item("DEN00001", ["DENYROOT"], title="SECRET-DENIED-TITLE-A"),
              item("DEN00002", ["DENYCHL1"], title="SECRET-DENIED-TITLE-B"),
              item("DEN00003", ["DENYGRC1"], title="SECRET-DENIED-TITLE-C")]
    fk, _ = basic(e, denied)
    r = zs.run_sync(e.settings, fk)
    txt = zs.render_report(r)
    check("T1 denied parent and descendants excluded (3), 1 eligible",
          r["counts"]["excluded_denied"] == 3 and r["counts"]["eligible"] == 1, r["counts"])
    check("T1 plan only contains the eligible item", [p["parent"]["key"] for p in r["plan"]] == ["PARENT01"])
    check("T1 no denied-item title text in report", "SECRET-DENIED" not in txt)
    check("T1 unconfigured denied grandchild warned about but still excluded",
          any("not listed in the config" in w for w in r["warnings"]))
    check("T1 cross-check ran over every denied collection",
          r["crosscheck"][0] == 3 and r["crosscheck"][1] >= 3, r["crosscheck"])

    # T2 in an allowed AND a denied collection
    e = fresh()
    fk, _ = basic(e, [item("BOTH0001", ["AAAAAAA2", "DENYCHL1"], title="SECRET-BOTH")])
    r = zs.run_sync(e.settings, fk)
    check("T2 item in allowed + denied collection is fully excluded",
          r["counts"]["excluded_denied"] == 1 and r["counts"]["excluded_denied_also_allowed"] == 1 and len(r["plan"]) == 1)

    # T3 unfiled / not allowlisted / trashed / group / standalone
    e = fresh()
    fk, _ = basic(e, [item("UNFILED1", []), item("OTHERCOL", ["OTHER001"]), item("TRASHED1", ["AAAAAAA1"]),
                      item("GROUP001", ["AAAAAAA1"], lib="group"), item("STANDALN", ["AAAAAAA1"], typ="attachment")])
    fk.trash = [item("TRASHED1", ["AAAAAAA1"])]
    r = zs.run_sync(e.settings, fk)
    c = r["counts"]
    check("T3 unfiled/unallowlisted/trashed/group/standalone excluded; 1 eligible",
          (c["unfiled"], c["not_allowlisted"], c["trashed"], c["excluded_group"], c["standalone_attachments"], c["eligible"]) == (1, 1, 1, 1, 1, 1), c)

    # T4 collection resolution failures
    e = fresh()
    fk, _ = basic(e)
    check("T4 missing allowed collection aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake([x for x in COLS() if x["key"] != "AAAAAAA2"], fk.items)), "not found"))
    check("T4 missing denied child (config deny key) aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake([x for x in COLS() if x["key"] != "DENYCHL1"], fk.items)), "not found"))
    check("T4 ambiguous allowed name aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake(COLS() + [col("DUPNAME1", "01 Foundations")], fk.items)), "ambiguous"))
    check("T4 two collections with the deny-root name abort",
          aborts(lambda: zs.run_sync(e.settings, Fake(COLS() + [col("DUPDENY1", "Excluded")], fk.items)), "ambiguous"))
    cols2 = COLS()
    cols2[1]["data"]["name"] = "Renamed"
    check("T4 renamed allowed collection aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake(cols2, fk.items)), "named differently"))
    cols3 = COLS()
    cols3[0]["data"]["parentCollection"] = "DENYROOT"
    check("T4 allowed collection nested under the denied root aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake(cols3, fk.items)), "overlaps"))
    cols4 = [x for x in COLS() if x["key"] != "DENYROOT"] + [col("NEWDENY1", "Excluded")]
    check("T4 live deny root has a different key than the config -> aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake(cols4, fk.items)), "not found"))

    # T5 incomplete API responses / pagination
    check("T5 short result (empty page before total) aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake(COLS(), fk.items, mode="short")), "incomplete"))
    e2 = fresh(page_size=2)
    many = [item(f"MANY000{i}", ["OTHER001"]) for i in range(5)] + [item("PARENT01", ["AAAAAAA2"])]
    check("T5 total drifting between pages aborts",
          aborts(lambda: zs.run_sync(e2.settings, Fake(COLS(), many, mode="drift")), "changed while"))
    check("T5 missing Total-Results aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake(COLS(), fk.items, mode="nototal")), "no total"))
    bad = item("NOCOLS01", ["AAAAAAA1"])
    del bad["data"]["collections"]
    check("T5 regular item without collections list aborts",
          aborts(lambda: zs.run_sync(e.settings, Fake(COLS(), fk.items + [bad])), "collections"))
    fkp = Fake(COLS(), many)
    res = zs.fetch_all(fkp, "/users/0/items", 2)
    check("T5 pagination spans pages (6 items, page size 2 -> 3 requests)",
          len(res) == 6 and sum("start=" in p for p in fkp.paths) == 3, fkp.paths)

    # T6 attachment problems
    e = fresh()
    good = e.pdf("ATTOK001", body=b"good-bytes")
    outside = e.tmp / "elsewhere" / "ATTOUT01" / "o.pdf"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"%PDF-1.4 outside")
    wrongfolder = e.pdf("SOMEOTHR", name="w.pdf", body=b"wrong-folder")
    fakedir = e.storage / "ATTFAKE1"
    fakedir.mkdir()
    (fakedir / "f.pdf").write_bytes(b"not a pdf at all")
    html = e.pdf("ATTHTML1", name="h.html", body=b"html")
    items = [item("PARENT01", ["AAAAAAA2"]), att("ATTOK001", "PARENT01", good),
             att("ATTNOHRF", "PARENT01", None), att("ATTLINK1", "PARENT01", good, mode="linked_file"),
             att("ATTHTML1", "PARENT01", html, ct="text/html"), att("ATTOUT01", "PARENT01", outside),
             att("ATTWRONG", "PARENT01", wrongfolder),
             att("ATTGONE1", "PARENT01", e.storage / "ATTGONE1" / "missing.pdf"),
             att("ATTFAKE1", "PARENT01", fakedir / "f.pdf")]
    r = zs.run_sync(e.settings, Fake(COLS(), items))
    a = r["att"]
    check("T6 only the good PDF is planned", a["would_copy"] == 1 and len(r["plan"]) == 1, a)
    check("T6 missing/linked/non-PDF/outside/missing-file/fake-PDF all skipped",
          (a["unresolved"], a["not_stored"], a["not_pdf"], a["outside_storage"]) == (2, 1, 2, 2), a)

    # T7 content duplicates (workspace + within one run)
    e = fresh()
    p1 = e.pdf("ATTOK001", body=b"same-bytes")
    p2 = e.pdf("ATTOK002", name="b.pdf", body=b"same-bytes")
    (e.root / "papers" / "Manual copy.pdf").write_bytes(p1.read_bytes())
    items = [item("PARENT01", ["AAAAAAA2"]), att("ATTOK001", "PARENT01", p1),
             item("PARENT02", ["AAAAAAA2"]), att("ATTOK002", "PARENT02", p2)]
    r = zs.run_sync(e.settings, Fake(COLS(), items), apply=True)
    check("T7 identical file already in workspace -> duplicates, nothing copied",
          r["att"]["content_duplicate"] == 2 and r["att"]["copied"] == 0 and not (e.root / "papers" / "zotero").exists(), r["att"])
    e = fresh()
    p1 = e.pdf("ATTOK001", body=b"same2")
    p2 = e.pdf("ATTOK002", name="b.pdf", body=b"same2")
    items = [item("PARENT01", ["AAAAAAA2"]), att("ATTOK001", "PARENT01", p1),
             item("PARENT02", ["AAAAAAA2"]), att("ATTOK002", "PARENT02", p2)]
    r = zs.run_sync(e.settings, Fake(COLS(), items))
    check("T7 two identical eligible sources: one copy planned, one duplicate",
          r["att"]["would_copy"] == 1 and r["att"]["content_duplicate"] == 1, r["att"])

    # T8 destination conflict, never overwritten
    e = fresh()
    fk, src = basic(e)
    dest = e.root / "papers" / "zotero" / "PARENT01" / "paper.pdf"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"DIFFERENT CONTENT")
    before = e.sha(dest)
    r = zs.run_sync(e.settings, fk, apply=True)
    check("T8 destination with different content = conflict, file untouched",
          r["att"]["conflict"] == 1 and r["att"]["copied"] == 0 and e.sha(dest) == before, r["att"])

    # T9 apply once, then manifest dedupe
    e = fresh()
    fk, src = basic(e)
    src_before = e.sha(src)
    snap0 = e.snapshot()
    zs.run_sync(e.settings, fk)
    check("T9 dry run writes nothing", snap0 == e.snapshot())
    r1 = zs.run_sync(e.settings, fk, apply=True)
    dest = e.root / "papers" / "zotero" / "PARENT01" / "paper.pdf"
    mlines = (e.root / "refs/zotero-sync/manifest.jsonl").read_text(encoding="utf-8").splitlines()
    check("T9 apply copies one file, checksum matches, Zotero original unchanged",
          r1["att"]["copied"] == 1 and dest.exists() and e.sha(dest) == e.sha(src) == src_before and src.exists())
    rec = json.loads(mlines[0])
    check("T9 manifest: 1 line keyed by attachment key with item key, collections, checksum, date, DOI, title",
          len(mlines) == 1 and rec["attachment_key"] == "ATTOK001" and rec["item_key"] == "PARENT01"
          and rec["collection_keys"] == ["AAAAAAA2"] and rec["sha256"] == src_before and rec["imported_at"]
          and rec["doi"] == "10.1/x" and rec["title"] == "Eligible Paper", rec)
    blob = json.dumps(rec) + zs.render_report(r1)
    check("T9 no library/links/header/account data in manifest or report",
          not any(s in blob for s in ("zotero.org", "99999", "12345", '"library"', '"links"', "Zotero-API", "Total-Results")))
    r2 = zs.run_sync(e.settings, fk, apply=True)
    check("T9 second apply: already imported, nothing copied, manifest still 1 line",
          r2["att"]["already_imported"] == 1 and r2["att"]["copied"] == 0
          and len((e.root / "refs/zotero-sync/manifest.jsonl").read_text().splitlines()) == 1)

    # T10 reports use exclusive create
    p_a = zs.save_report(e.settings, "x", r1["now"])
    p_b = zs.save_report(e.settings, "y", r1["now"])
    check("T10 reports use exclusive create (same-second report gets a new name)",
          p_a != p_b and p_a.read_text().strip() == "x")

    # T11 imported items that later become ineligible keep their files
    items2 = copy.deepcopy(fk.items)
    items2[0]["data"]["collections"] = ["DENYROOT"]
    r = zs.run_sync(e.settings, Fake(COLS(), items2))
    t = zs.render_report(r)
    check("T11 item moved into a denied collection after import: reported, local file kept, no title in that section",
          "is now in an excluded collection" in t and dest.exists()
          and "Eligible Paper" not in t.split("PREVIOUSLY")[1] and r["att"]["copied"] == 0)
    r = zs.run_sync(e.settings, Fake(COLS(), fk.items, trash=[fk.items[0]]))
    check("T11 trashed after import: reported, file kept",
          any("trash" in s for _, _, s in r["review"]) and dest.exists())
    r = zs.run_sync(e.settings, Fake(COLS(), []))
    check("T11 deleted from Zotero: reported, file kept",
          any("not found" in s for _, _, s in r["review"]) and dest.exists())

    # T12 cross-check catches an inconsistent exclusion
    e = fresh()
    fk, _ = basic(e)
    ghost = item("GHOST001", ["AAAAAAA1"], title="SECRET-GHOST")
    fk2 = Fake(COLS(), fk.items, coll_items=lambda k: [ghost] if k == "DENYCHL1" else [])
    check("T12 deny cross-check failure aborts before any copy",
          aborts(lambda: zs.run_sync(e.settings, fk2, apply=True), "could not be verified")
          and not (e.root / "papers" / "zotero").exists())

    # T13 Zotero unavailable
    check("T13 closed port -> ZoteroUnavailable",
          aborts(lambda: zs.ApiClient("http://127.0.0.1:1/api", 2).get("/users/0/collections?limit=1"),
                 "cannot reach", zs.ZoteroUnavailable))
    e = fresh()
    cfgp = Path(tmp) / "unavail.json"
    example = json.loads(zs.EXAMPLE_CONFIG.read_text(encoding="utf-8"))
    example.update(api_base="http://127.0.0.1:1/api", timeout_seconds=2, zotero_storage_dir=str(e.storage))
    cfgp.write_text(json.dumps(example), encoding="utf-8")
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = zs.main(["--config", str(cfgp)])
    check("T13 main() exits 3 with a clear message when Zotero is unavailable",
          code == 3 and "Nothing was copied" in err.getvalue(), (code, err.getvalue()))
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = zs.main(["--config", str(Path(tmp) / "does-not-exist.json")])
    check("T13 main() exits 4 with a helpful message when the config is missing",
          code == 4 and "example" in err.getvalue(), (code, err.getvalue()))

    # T14 client guards
    check("T14 non-127.0.0.1 api_base rejected", aborts(lambda: zs.ApiClient("http://example.com/api")))
    check("T14 localhost-name and https bases rejected",
          aborts(lambda: zs.ApiClient("http://localhost:23119/api")) and aborts(lambda: zs.ApiClient("https://127.0.0.1:23119/api")))
    cl = zs.ApiClient("http://127.0.0.1:23119/api")
    check("T14 requests outside the read-only allowlist refused",
          aborts(lambda: cl.get("/users/0/settings"), "allowlist") and aborts(lambda: cl.get("/better-bibtex/export"), "allowlist"))
    src_text = Path(zs.__file__).read_text(encoding="utf-8")
    check("T14 source: GET only; no sqlite import; no Better BibTeX URLs",
          'method="GET"' in src_text and "import sqlite3" not in src_text and src_text.count("Request(") == 1
          and ".open(req" in src_text
          and not any(w in src_text for w in ('method="POST"', 'method="PUT"', 'method="DELETE"', "http://127.0.0.1:23119/better")))

    # T15 config validation (uses the committed example config, so this works anywhere)
    def variant(mut):
        d = json.loads(zs.EXAMPLE_CONFIG.read_text(encoding="utf-8"))
        mut(d)
        pth = Path(tmp) / "v.json"
        pth.write_text(json.dumps(d), encoding="utf-8")
        return lambda: zs.load_settings(pth)
    s = zs.load_settings(zs.EXAMPLE_CONFIG)
    check("T15 example config loads: 4 allow keys, 3 deny keys", len(s.allow) == 4 and len(s.deny) == 3)
    check("T15 unknown config key rejected", aborts(variant(lambda d: d.update(typo=1)), "unknown"))
    check("T15 dest_dir outside papers/ rejected", aborts(variant(lambda d: d.update(dest_dir="notes/papers")), "inside papers"))
    check("T15 allow/deny overlap rejected", aborts(variant(lambda d: d["deny"].append(d["allow"][0])), "more than once"))
    check("T15 deny list without the root rejected", aborts(variant(lambda d: d.update(deny=d["deny"][1:])), "root"))

    # T16 filename safety
    check("T16 safe_filename: invalid chars, reserved names, long names",
          zs.safe_filename('a<b>:c?.pdf', 100) == "a_b__c_.pdf" and zs.safe_filename("CON.pdf", 100) == "_CON.pdf"
          and len(zs.safe_filename("x" * 300 + ".pdf", 50)) <= 50)

    # T17 standalone note without a collections list
    e = fresh()
    fk, _ = basic(e)
    note = item("NOTE0001", ["AAAAAAA1"], typ="note")
    note["data"]["collections"] = None
    check("T17 standalone note without collections handled",
          zs.run_sync(e.settings, Fake(COLS(), fk.items + [note]))["counts"]["standalone_notes"] == 1)

    # T18 items in several collections are counted and copied once
    e = fresh()
    p = e.pdf("ATTMULTI", body=b"multi-collection")
    items = [item("MULTI001", ["AAAAAAA1", "AAAAAAA2"], title="In two allowed collections"), att("ATTMULTI", "MULTI001", p)]
    denied_multi = [item(f"DENM000{i}", ["DENYROOT", "DENYCHL1"], title=f"SECRET-{i}") for i in range(3)]
    fk = Fake(COLS(), items + denied_multi)
    r = zs.run_sync(e.settings, fk, apply=True)
    mlines = (e.root / "refs/zotero-sync/manifest.jsonl").read_text(encoding="utf-8").splitlines()
    check("T18 item in 2 allowed collections: 1 eligible, 1 copy, 1 manifest record listing both collections",
          r["counts"]["eligible"] == 1 and r["att"]["copied"] == 1 and len(mlines) == 1
          and json.loads(mlines[0])["collection_keys"] == ["AAAAAAA1", "AAAAAAA2"], (r["counts"], r["att"], mlines))
    check("T18 3 denied items each in 2 denied collections: counted as 3 items, cross-check saw 6 listings",
          r["counts"]["excluded_denied"] == 3 and r["crosscheck"][1] >= 6, (r["counts"], r["crosscheck"]))

    # T19-T25 generated index
    def index_env():
        e = fresh()
        p1 = e.pdf("ATTIDX01", body=b"idx-one")
        p2 = e.pdf("ATTIDX02", name="two.pdf", body=b"idx-two")
        (e.root / "papers" / "Manual two.pdf").write_bytes(p2.read_bytes())
        cols = COLS() + [col("AAAAAAC1", "Sub", "AAAAAAA2")]
        items = [item("IDXITEM1", ["AAAAAAA1", "AAAAAAA2"], title="Paper One", date="2021"), att("ATTIDX01", "IDXITEM1", p1),
                 item("IDXITEM2", ["AAAAAAC1"], title="Paper Two In Sub", date="2019"), att("ATTIDX02", "IDXITEM2", p2),
                 item("IDXITEM3", ["AAAAAAA2"], title="No PDF Paper"),
                 item("SECRET01", ["DENYROOT"], title="SECRET-DENIED-IDX"), item("UNFILED9", [], title="UNFILED-TITLE"),
                 item("OTHERC09", ["OTHER001"], title="MISC-ONLY-TITLE")]
        return e, Fake(cols, items)
    e, fk = index_env()
    idx = e.root / "refs/zotero-sync/index.md"
    r = zs.run_sync(e.settings, fk)
    check("T19 dry run does not create the index and says so", not idx.exists() and "would be regenerated" in zs.render_report(r))
    r = zs.run_sync(e.settings, fk, apply=True)
    t = idx.read_text(encoding="utf-8")
    check("T19 apply creates the index with a generated-by header",
          r["index_status"] == "updated" and t.startswith("<!-- generated-by: scripts/zotero_sync.py | sha256-of-body: "))
    check("T20 grouped by collection, subcollection path shown, item in 2 collections listed under both",
          "## 00 Inbox (1)" in t and "## 01 Foundations (2)" in t and "## 01 Foundations > Sub (1)" in t
          and t.count("`IDXITEM1`") == 2, t)
    check("T20 PDF locations: copied file, and matching workspace duplicate; item without PDF says so",
          "papers/zotero/IDXITEM1/paper.pdf" in t and "papers/Manual two.pdf" in t and "no PDF in this workspace" in t, t)
    check("T20 'also in' lists the other allowed collection", "also in: 01 Foundations" in t and "also in: 00 Inbox" in t)
    check("T21 index has no denied items, no denied collection names, no unfiled/unallowlisted items",
          not any(s in t for s in ("SECRET", "Excluded", "Child One", "UNFILED-TITLE", "MISC-ONLY", "Misc")), t)
    later = r["now"] + datetime.timedelta(days=1)
    r2 = zs.run_sync(e.settings, fk, apply=True, now=later)
    check("T22 re-apply regenerates an unedited generated index",
          r2["index_status"] in ("updated", "unchanged") and idx.read_text(encoding="utf-8").startswith("<!-- generated-by"))
    edited = idx.read_text(encoding="utf-8") + "\nMy own note\n"
    idx.write_text(edited, encoding="utf-8")
    r3 = zs.run_sync(e.settings, fk, apply=True, now=later + datetime.timedelta(days=1))
    check("T23 hand-edited index is never overwritten",
          r3["index_status"].startswith("NOT updated") and idx.read_text(encoding="utf-8") == edited)
    e2, fk2_ = index_env()
    idx2 = e2.root / "refs/zotero-sync/index.md"
    idx2.parent.mkdir(parents=True)
    idx2.write_text("hand-written index", encoding="utf-8")
    r4 = zs.run_sync(e2.settings, fk2_, apply=True)
    check("T24 a pre-existing non-generated index.md is never overwritten",
          r4["index_status"].startswith("NOT updated") and idx2.read_text() == "hand-written index"
          and r4["att"]["copied"] == 1 and r4["att"]["content_duplicate"] == 1, r4["att"])
    e3, fk3_ = index_env()
    leftover = e3.root / "refs/zotero-sync/index.md.tmp"
    leftover.parent.mkdir(parents=True)
    leftover.write_text("stale", encoding="utf-8")
    r5 = zs.run_sync(e3.settings, fk3_, apply=True)
    check("T25 leftover .tmp blocks the write and is left untouched",
          r5["index_status"].startswith("NOT updated") and leftover.read_text() == "stale"
          and not (e3.root / "refs/zotero-sync/index.md").exists())
finally:
    shutil.rmtree(tmp, ignore_errors=True)

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} passed, {len(fails)} failed of {len(RESULTS)}")
sys.exit(1 if fails else 0)
