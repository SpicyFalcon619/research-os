#!/usr/bin/env python3
"""Copy eligible PDFs from Zotero into this workspace via Zotero's local API.

Standard library only. Dry run is the default; only --apply copies files.

Safety model (see scripts/zotero_sync_config.json):
  * Zotero is read through GET requests to 127.0.0.1 only. The SQLite database
    and Better BibTeX are never touched. Response headers, 'library' objects
    and 'links' objects are never printed or stored.
  * Only the allowlisted collections (and their descendants) are eligible.
    The deny collection(s) and all descendants always win. An item in
    any denied collection is excluded entirely.
  * Anything doubtful aborts the run before any copy (fail closed).
  * Files are never overwritten, moved or deleted. Copies use exclusive create.
  * Notes, the literature matrix and triage are never touched.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.request import url2pathname

ROOT = Path(__file__).resolve().parent.parent
# Your real collection keys and names live in the git-ignored local file; the committed
# example holds placeholders only.
DEFAULT_CONFIG = ROOT / "scripts" / "zotero_sync_config.local.json"
EXAMPLE_CONFIG = ROOT / "scripts" / "zotero_sync_config.example.json"

API_PREFIXES = ("/users/0/collections", "/users/0/items", "/users/0/groups")
KEY_RE = re.compile(r"^[A-Z0-9]{8}$")
NON_REGULAR = {"attachment", "note", "annotation"}
STORED_LINK_MODES = {"imported_file", "imported_url"}
MAX_PATH_LEN = 240
REQUIRED_CONFIG = {"api_base", "zotero_storage_dir", "dest_dir", "manifest", "reports_dir",
                   "duplicate_scan_dirs", "deny_root_name", "allow", "deny"}
OPTIONAL_CONFIG = {"page_size", "timeout_seconds", "index"}

EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_UNAVAILABLE, EXIT_ABORT = 0, 1, 2, 3, 4


class SyncAbort(Exception):
    """A safety check failed. Nothing was copied."""


class ZoteroUnavailable(SyncAbort):
    """Zotero's local API could not be reached or refused the request."""


# ----------------------------------------------------------------- settings

class Settings:
    def __init__(self, cfg, root):
        self.root = Path(root).resolve()
        self.api_base = cfg["api_base"]
        self.page_size = int(cfg.get("page_size", 100))
        self.timeout = int(cfg.get("timeout_seconds", 20))
        if not 1 <= self.page_size <= 100:
            raise SyncAbort("config: page_size must be 1-100")
        self.storage = Path(os.path.expanduser(cfg["zotero_storage_dir"])).resolve()
        self.dest_dir = self._inside_root(cfg["dest_dir"], must_be_under="papers")
        self.manifest = self._inside_root(cfg["manifest"])
        self.index = self._inside_root(cfg.get("index", "refs/zotero-sync/index.md"))
        self.reports_dir = self._inside_root(cfg["reports_dir"])
        self.scan_dirs = [self._inside_root(d) for d in cfg["duplicate_scan_dirs"]]
        self.deny_root_name = cfg["deny_root_name"]
        self.allow = self._entries(cfg["allow"], "allow")
        self.deny = self._entries(cfg["deny"], "deny")
        if not self.allow:
            raise SyncAbort("config: 'allow' must list at least one collection")
        if not any(e["name"] == self.deny_root_name for e in self.deny):
            raise SyncAbort(f"config: 'deny' must include the root collection '{self.deny_root_name}'")
        keys = [e["key"] for e in self.allow + self.deny]
        if len(keys) != len(set(keys)):
            raise SyncAbort("config: a collection key appears more than once")
        if {e["key"] for e in self.allow} & {e["key"] for e in self.deny}:
            raise SyncAbort("config: a collection is both allowed and denied")

    def _inside_root(self, rel, must_be_under=None):
        p = (self.root / rel).resolve()
        base = self.root / must_be_under if must_be_under else self.root
        try:
            p.relative_to(base.resolve())
        except ValueError:
            raise SyncAbort(f"config: path '{rel}' must stay inside {must_be_under or 'the workspace'}")
        return p

    @staticmethod
    def _entries(entries, label):
        out = []
        for e in entries:
            if not (isinstance(e, dict) and KEY_RE.match(str(e.get("key", ""))) and e.get("name")):
                raise SyncAbort(f"config: bad '{label}' entry; need an 8-character key and a name")
            out.append({"key": e["key"], "name": e["name"]})
        return out


def load_settings(config_path=DEFAULT_CONFIG, root=ROOT):
    if not Path(config_path).exists():
        raise SyncAbort("config file not found: copy scripts/zotero_sync_config.example.json to "
                        "scripts/zotero_sync_config.local.json and fill in your own collection keys and names")
    try:
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SyncAbort(f"cannot read config ({type(exc).__name__})")
    present = {k for k in cfg if not k.startswith("_")}
    if missing := REQUIRED_CONFIG - present:
        raise SyncAbort(f"config: missing {sorted(missing)}")
    if unknown := present - REQUIRED_CONFIG - OPTIONAL_CONFIG:
        raise SyncAbort(f"config: unknown keys {sorted(unknown)}")
    return Settings(cfg, root)


# ---------------------------------------------------------------------- API

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ApiClient:
    """GET-only client for Zotero's local API. Never returns or logs headers."""

    def __init__(self, base, timeout=20):
        u = urllib.parse.urlparse(base)
        if u.scheme != "http" or u.hostname != "127.0.0.1":
            raise SyncAbort("api_base must be http://127.0.0.1:<port>/api")
        self.base = base.rstrip("/")
        self.timeout = timeout
        self._opener = urllib.request.build_opener(_NoRedirect)

    def get(self, path):
        """Return (parsed JSON, Total-Results as int or None)."""
        if not path.startswith(API_PREFIXES):
            raise SyncAbort("internal: refusing a request outside the read-only allowlist")
        req = urllib.request.Request(self.base + path, headers={"Zotero-API-Version": "3"}, method="GET")
        try:
            with self._opener.open(req, timeout=self.timeout) as resp:
                body = resp.read()
                total = resp.headers.get("Total-Results")
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise ZoteroUnavailable(
                    "Zotero refused the request (HTTP 403). Enable Zotero Settings > Advanced > "
                    "'Allow other applications on this computer to communicate with Zotero'.")
            raise ZoteroUnavailable(f"Zotero's API answered HTTP {exc.code} for {path.split('?')[0]}")
        except (urllib.error.URLError, OSError, TimeoutError):
            raise ZoteroUnavailable("Cannot reach Zotero's local API on 127.0.0.1. Is Zotero running?")
        try:
            data = json.loads(body)
        except ValueError:
            raise SyncAbort("Zotero's API returned something that is not JSON")
        return data, (int(total) if total is not None and total.isdigit() else None)


def fetch_all(client, path, page_size=100):
    """Fetch every page of a list endpoint; abort if the result is not demonstrably complete."""
    sep = "&" if "?" in path else "?"
    out, start, total = [], 0, None
    while True:
        page, t = client.get(f"{path}{sep}limit={page_size}&start={start}")
        if not isinstance(page, list):
            raise SyncAbort("incomplete API response: expected a list")
        if t is None:
            raise SyncAbort("incomplete API response: no total count")
        if total is None:
            total = t
        elif t != total:
            raise SyncAbort("the Zotero library changed while it was being read; run again")
        out.extend(page)
        if len(out) >= total:
            break
        if not page:
            raise SyncAbort("incomplete API response: ran out of pages before the reported total")
        start += len(page)
    keys = [o.get("key") for o in out]
    if len(out) != total or len(set(keys)) != len(keys):
        raise SyncAbort("incomplete or inconsistent API response (count or duplicate keys)")
    return out


# -------------------------------------------------------------- collections

def resolve_collections(cols, settings):
    """Check configured keys against the live tree; return (allow_set, deny_set, names, warnings)."""
    live = {}
    for c in cols:
        key, name = c.get("key"), (c.get("data") or {}).get("name")
        if not (isinstance(key, str) and KEY_RE.match(key)) or name is None:
            raise SyncAbort("incomplete API response: collection without a valid key or name")
        if key in live:
            raise SyncAbort("API returned the same collection twice")
        if not c["data"].get("deleted"):
            live[key] = c
    name_counts = {}
    for c in live.values():
        name_counts[c["data"]["name"]] = name_counts.get(c["data"]["name"], 0) + 1

    def check(entry, role):
        c = live.get(entry["key"])
        if c is None:
            raise SyncAbort(f"{role} collection '{entry['name']}' ({entry['key']}) was not found in Zotero")
        if c["data"]["name"] != entry["name"]:
            raise SyncAbort(f"{role} collection {entry['key']} is now named differently than the config says")
        if name_counts[entry["name"]] != 1:
            raise SyncAbort(f"{role} collection name '{entry['name']}' is ambiguous (used more than once)")
        return entry["key"]

    allow_roots = [check(e, "allow") for e in settings.allow]
    deny_cfg = [check(e, "deny") for e in settings.deny]
    roots = [k for k, c in live.items() if c["data"]["name"] == settings.deny_root_name]
    if len(roots) != 1:
        raise SyncAbort(f"expected exactly one '{settings.deny_root_name}' collection, found {len(roots)}")
    if roots[0] not in deny_cfg:
        raise SyncAbort(f"the live '{settings.deny_root_name}' collection key is not in the config deny list")

    children = {}
    for k, c in live.items():
        children.setdefault(c["data"].get("parentCollection") or None, []).append(k)

    def descendants(root):
        seen, stack = set(), [root]
        while stack:
            k = stack.pop()
            if k not in seen:
                seen.add(k)
                stack.extend(children.get(k, []))
        return seen

    deny_set = set().union(*(descendants(k) for k in deny_cfg))
    allow_set = set().union(*(descendants(k) for k in allow_roots))
    if allow_set & deny_set:
        raise SyncAbort("an allowed collection overlaps the denied tree; refusing to continue")
    warnings = []
    if extra := deny_set - set(deny_cfg):
        warnings.append(f"{len(extra)} collection(s) under the denied tree are not listed in the config "
                        "(they are excluded anyway); add their keys to the config deny list")
    names = {k: c["data"]["name"] for k, c in live.items()}
    return allow_set, deny_set, names, warnings


# ------------------------------------------------------------ item helpers

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def safe_filename(name, max_len):
    stem = _INVALID.sub("_", os.path.splitext(Path(name).name)[0]).strip(" .") or "attachment"
    if stem.lower() in _RESERVED:
        stem = "_" + stem
    stem = stem[:max(1, max_len - 4)].rstrip(" .") or "attachment"
    return stem + ".pdf"


def year_of(item):
    parsed = (item.get("meta") or {}).get("parsedDate") or ""
    m = re.match(r"(\d{4})", parsed) or re.search(r"\b(1[89]\d\d|20\d\d)\b", item["data"].get("date") or "")
    return int(m.group(1)) if m else None


def first_author(item):
    for c in item["data"].get("creators") or []:
        return c.get("lastName") or c.get("name") or ""
    return ""


def classify_items(items, allow_set, deny_set, trash_keys):
    """Sort top-level items into eligible / excluded buckets using collection keys only."""
    c = dict(eligible=0, excluded_denied=0, excluded_denied_also_allowed=0, unfiled=0, not_allowlisted=0,
             trashed=0, excluded_group=0, standalone_attachments=0, standalone_notes=0)
    eligible, denied_members = {}, set()
    for it in items:
        d = it.get("data") or {}
        typ = d.get("itemType")
        if typ == "annotation" or d.get("parentItem"):
            continue
        key = it.get("key")
        if not (isinstance(key, str) and KEY_RE.match(key)):
            raise SyncAbort("incomplete API response: item without a valid key")
        if (it.get("library") or {}).get("type") != "user":
            c["excluded_group"] += 1
            continue
        cols = d.get("collections")
        if cols is None and typ in NON_REGULAR:
            cols = []
        if not isinstance(cols, list):
            raise SyncAbort("incomplete API response: item without a collections list")
        cs = set(cols)
        if cs & deny_set:
            denied_members.add(key)
            c["excluded_denied"] += 1
            if cs & allow_set:
                c["excluded_denied_also_allowed"] += 1
            continue
        if typ == "note":
            c["standalone_notes"] += 1
            continue
        if typ == "attachment":
            c["standalone_attachments"] += 1
            continue
        if key in trash_keys or d.get("deleted"):
            c["trashed"] += 1
        elif not cs:
            c["unfiled"] += 1
        elif cs & allow_set:
            eligible[key] = it
            c["eligible"] += 1
        else:
            c["not_allowlisted"] += 1
    return c, eligible, denied_members


def crosscheck_deny(client, deny_set, denied_members, trash_keys, page_size):
    """Independently list each denied collection and confirm every member was excluded."""
    seen = 0
    for ck in sorted(deny_set):
        if not KEY_RE.match(ck):
            raise SyncAbort("deny cross-check: invalid collection key")
        for m in fetch_all(client, f"/users/0/collections/{ck}/items/top?include=data", page_size):
            seen += 1
            if m.get("key") not in denied_members and m.get("key") not in trash_keys:
                raise SyncAbort("exclusion could not be verified: an item listed in a denied "
                                f"collection ({ck}) was not classified as excluded (item {m.get('key')})")
    return seen


def resolve_attachment(att, storage):
    """Return (resolved Path, None) or (None, reason)."""
    d = att.get("data") or {}
    if att.get("key") in (None, "") or not KEY_RE.match(att["key"]):
        return None, "unresolved"
    if d.get("contentType") != "application/pdf":
        return None, "not_pdf"
    if d.get("linkMode") not in STORED_LINK_MODES:
        return None, "not_stored"
    href = ((att.get("links") or {}).get("enclosure") or {}).get("href")
    if not isinstance(href, str) or not href.startswith("file:"):
        return None, "unresolved"
    u = urllib.parse.urlparse(href)
    if u.netloc not in ("", "localhost"):
        return None, "outside_storage"
    try:
        p = Path(url2pathname(u.path)).resolve()
    except (OSError, ValueError):
        return None, "unresolved"
    if p.parent.parent != storage or p.parent.name != att["key"]:
        return None, "outside_storage"
    if not p.is_file():
        return None, "unresolved"
    try:
        with open(p, "rb") as f:
            if f.read(5) != b"%PDF-":
                return None, "not_pdf"
    except OSError:
        return None, "unresolved"
    return p, None


def index_pdfs(dirs, wanted_sizes):
    """Map sha256 -> [paths] for workspace PDFs whose size matches a source PDF."""
    found = {}
    for base in dirs:
        if not base.is_dir():
            continue
        for dirpath, _, names in os.walk(base):
            for n in names:
                p = Path(dirpath) / n
                if not n.lower().endswith(".pdf") or p.is_symlink():
                    continue
                try:
                    if p.stat().st_size in wanted_sizes:
                        found.setdefault(sha256_file(p), []).append(p)
                except OSError:
                    continue
    return found


def load_manifest(path):
    recs = {}
    if not path.exists():
        return recs
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                raise SyncAbort(f"manifest line {n} is not valid JSON; fix or move it by hand")
            if not isinstance(r, dict) or not KEY_RE.match(str(r.get("attachment_key", ""))):
                raise SyncAbort(f"manifest line {n} has no valid attachment_key")
            recs[r["attachment_key"]] = r
    return recs


def manifest_record(parent, att, names, src, dest, sha, size, settings, now):
    d, ad = parent["data"], att["data"]
    pub = d.get("proceedingsTitle") or d.get("publicationTitle") or d.get("bookTitle") or ""
    cks = sorted(d.get("collections") or [])
    return {
        "attachment_key": att["key"], "item_key": parent["key"], "item_type": d.get("itemType"),
        "title": d.get("title", ""),
        "creators": [{k: c[k] for k in ("creatorType", "firstName", "lastName", "name") if k in c}
                     for c in d.get("creators") or []],
        "date": d.get("date", ""), "year": year_of(parent), "doi": d.get("DOI", ""), "url": d.get("url", ""),
        "publication": pub, "citation_key": d.get("citationKey", ""),
        "collection_keys": cks, "collection_names": [names.get(k, "") for k in cks],
        "attachment": {k: ad.get(k) for k in ("contentType", "linkMode", "filename", "md5", "mtime")},
        "zotero_item_version": d.get("version"),
        "source": f"storage/{att['key']}/{src.name}",
        "dest": dest.relative_to(settings.root).as_posix(),
        "sha256": sha, "size": size, "imported_at": now.isoformat(timespec="seconds"),
    }


def review_manifest(manifest, index, deny_set, allow_set, trash_keys):
    """Report previously imported items that are no longer eligible. Files are never touched."""
    out = []
    for ak, r in sorted(manifest.items()):
        ik = r.get("item_key")
        it = index.get(ik)
        if ik in trash_keys:
            status = "is now in the Zotero trash"
        elif it is None:
            status = "was not found in Zotero"
        else:
            d = it["data"]
            cs = set(d.get("collections") or [])
            if cs & deny_set:
                status = "is now in an excluded collection"
            elif d.get("deleted"):
                status = "is now in the Zotero trash"
            elif not cs:
                status = "is now unfiled"
            elif not cs & allow_set:
                status = "is no longer in an allowed collection"
            else:
                continue
        out.append((ak, ik, status))
    return out


# -------------------------------------------------------------------- index

INDEX_HEADER_RE = re.compile(rb"^<!-- generated-by: scripts/zotero_sync\.py \| sha256-of-body: ([0-9a-f]{64}) -->$")


def build_index_entries(eligible, allow_set, cols, atts_by_parent, placed, settings):
    """Eligible items grouped by allowed collection. Never includes denied or unfiled items."""
    live = {c["key"]: c for c in cols if not (c.get("data") or {}).get("deleted")}

    def path_of(key):
        parts, seen = [], set()
        while key and key in live and key not in seen:
            seen.add(key)
            parts.append(live[key]["data"]["name"])
            key = live[key]["data"].get("parentCollection") or None
        return " > ".join(reversed(parts))

    order = {e["key"]: i for i, e in enumerate(settings.allow)}
    groups = {}
    for pkey, parent in eligible.items():
        d = parent["data"]
        mine = sorted(k for k in d["collections"] if k in allow_set)
        pdfs = sorted(p for a in atts_by_parent.get(pkey, []) if (p := placed.get(a["key"])))
        for ck in mine:
            groups.setdefault(ck, []).append({
                "key": pkey, "year": year_of(parent), "author": first_author(parent), "title": d.get("title", ""),
                "also": [path_of(k) for k in mine if k != ck], "pdfs": pdfs})
    root_of = lambda k: next((order[r] for r in order if r == k or path_of(k).startswith(path_of(r) + " > ")), len(order))
    return [(path_of(k), sorted(groups[k], key=lambda e: (-(e["year"] or 0), e["author"], e["title"])))
            for k in sorted(groups, key=lambda k: (root_of(k), path_of(k)))]


def render_index(entries, now):
    total = len({e["key"] for _, items in entries for e in items})
    lines = ["# Zotero index", "",
             f"Generated {now.strftime('%Y-%m-%d %H:%M')} from Zotero by `scripts/zotero_sync.py`. "
             f"{total} paper(s) in the allowed collections. Zotero is the source of truth; this file only lists "
             "papers and where their PDF is in this workspace. Do not edit it by hand: it is regenerated on each "
             "`--apply`, and a hand-edited copy is never overwritten.", ""]
    if not entries:
        lines.append("_No papers in the allowed collections._")
    for name, items in entries:
        lines += [f"## {name} ({len(items)})", ""]
        for e in items:
            who = f"{e['author'] or 'Unknown author'} ({e['year'] or 'n.d.'})"
            lines.append(f"- **{who}**: {e['title'] or '(untitled)'}")
            pdf = ", ".join(f"`{p}`" for p in e["pdfs"]) if e["pdfs"] else "no PDF in this workspace"
            extra = f" · also in: {'; '.join(e['also'])}" if e["also"] else ""
            lines.append(f"  - Zotero item `{e['key']}`{extra} · PDF: {pdf}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def write_index(path, text):
    """Write the generated index. Only a file this script generated and nobody edited may be replaced."""
    body = text.encode("utf-8")
    header = b"<!-- generated-by: scripts/zotero_sync.py | sha256-of-body: " + hashlib.sha256(body).hexdigest().encode() + b" -->\n"
    try:
        if path.exists():
            current = path.read_bytes()
            first, _, rest = current.partition(b"\n")
            m = INDEX_HEADER_RE.match(first)
            if not m or hashlib.sha256(rest).hexdigest().encode() != m.group(1):
                return ("NOT updated: the existing index file was not generated by this script or was edited by "
                        "hand; move it aside to regenerate")
            if current == header + body:
                return "unchanged"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "xb") as f:  # 'x': never clobber an unexpected file
            f.write(header + body)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return "updated"
    except FileExistsError:
        return "NOT updated: a leftover index .tmp file exists; remove it by hand"
    except OSError as exc:
        return f"NOT updated: {exc.__class__.__name__}"


# --------------------------------------------------------------------- sync

def run_sync(settings, client, apply=False, now=None):
    """Plan (and with apply=True, perform) the sync. Raises SyncAbort before any copy on doubt."""
    now = now or datetime.datetime.now().astimezone()
    if not settings.storage.is_dir() or settings.storage.name.lower() != "storage":
        raise SyncAbort("Zotero storage directory not found or not named 'storage'; check zotero_storage_dir")
    ps = settings.page_size

    cols = fetch_all(client, "/users/0/collections", ps)
    allow_set, deny_set, names, warnings = resolve_collections(cols, settings)
    items = fetch_all(client, "/users/0/items?include=data", ps)
    trash_keys = {t.get("key") for t in fetch_all(client, "/users/0/items/trash?include=data", ps)}
    try:
        groups = client.get("/users/0/groups?limit=1")[1]
    except SyncAbort:
        groups = None

    index = {it["key"]: it for it in items if isinstance(it.get("key"), str)}
    counts, eligible, denied_members = classify_items(items, allow_set, deny_set, trash_keys)
    crosscheck_n = crosscheck_deny(client, deny_set, denied_members, trash_keys, ps)

    atts_by_parent, orphans = {}, 0
    for it in items:
        d = it.get("data") or {}
        if d.get("itemType") == "attachment" and d.get("parentItem"):
            if d["parentItem"] in index:
                atts_by_parent.setdefault(d["parentItem"], []).append(it)
            else:
                orphans += 1

    a = dict(attachments=0, would_copy=0, copied=0, already_imported=0, content_duplicate=0, conflict=0,
             changed_in_zotero=0, imported_file_missing=0, local_file_differs=0, not_pdf=0, not_stored=0,
             outside_storage=0, unresolved=0, trashed=0, no_attachment=0, orphans=orphans, errors=0)
    manifest = load_manifest(settings.manifest)
    resolved = []
    for pkey in sorted(eligible):
        parent = eligible[pkey]
        # Defence in depth: nothing from a denied collection may ever reach the plan.
        if set(parent["data"]["collections"]) & deny_set or not set(parent["data"]["collections"]) & allow_set:
            raise SyncAbort("internal consistency check failed for an eligible item")
        atts = sorted(atts_by_parent.get(pkey, []), key=lambda x: x["key"])
        if not atts:
            a["no_attachment"] += 1
        for att in atts:
            a["attachments"] += 1
            if att["key"] in trash_keys or att["data"].get("deleted"):
                a["trashed"] += 1
                continue
            src, reason = resolve_attachment(att, settings.storage)
            if reason:
                a[reason] += 1
                continue
            resolved.append((parent, att, src))

    sizes = {src.stat().st_size for _, _, src in resolved}
    workspace = index_pdfs(settings.scan_dirs, sizes)
    details, plan, planned_hashes = [], [], {}
    placed = {}  # attachment key -> workspace-relative path of its PDF, for the index
    for parent, att, src in resolved:
        ak, pk = att["key"], parent["key"]
        sha, size = sha256_file(src), src.stat().st_size
        folder = settings.dest_dir / pk
        room = MAX_PATH_LEN - len(str(folder)) - 1
        if room < 16:
            a["unresolved"] += 1
            details.append(("unresolved", ak, "destination path would be too long"))
            continue
        dest = folder / safe_filename(src.name, room)
        rel = dest.relative_to(settings.root).as_posix()
        rec = manifest.get(ak)
        if rec:
            recorded = (settings.root / rec["dest"]).resolve()
            if settings.root not in recorded.parents:
                raise SyncAbort("manifest points outside the workspace; fix or move it by hand")
            if not recorded.exists():
                a["imported_file_missing"] += 1
                details.append(("imported_file_missing", ak, f"imported copy is missing locally ({rec['dest']}); not re-copied"))
            elif sha256_file(recorded) != rec["sha256"]:
                a["local_file_differs"] += 1
                placed[ak] = rec["dest"]
                details.append(("local_file_differs", ak, f"local copy differs from the manifest ({rec['dest']}); left alone"))
            elif sha != rec["sha256"]:
                a["changed_in_zotero"] += 1
                placed[ak] = rec["dest"]
                details.append(("changed_in_zotero", ak, "the PDF changed in Zotero since import; local copy kept, not overwritten"))
            else:
                a["already_imported"] += 1
                placed[ak] = rec["dest"]
            continue
        same = workspace.get(sha, [])
        if sha in planned_hashes:
            a["content_duplicate"] += 1
            placed[ak] = placed.get(planned_hashes[sha])
            details.append(("content_duplicate", ak, f"identical to {planned_hashes[sha]} in this run; no copy"))
        elif same:
            a["content_duplicate"] += 1
            where = same[0].relative_to(settings.root).as_posix() if settings.root in same[0].parents else "(outside workspace)"
            if where != "(outside workspace)":
                placed[ak] = where
            details.append(("content_duplicate", ak, f"identical file already exists at {where}; no copy"))
        elif dest.exists():
            if dest.is_file() and sha256_file(dest) == sha:
                a["content_duplicate"] += 1
                placed[ak] = rel
                details.append(("content_duplicate", ak, f"identical file already exists at {rel} (not in manifest); no copy"))
            else:
                a["conflict"] += 1
                details.append(("conflict", ak, f"destination exists with different content ({rel}); skipped"))
        else:
            a["would_copy"] += 1
            planned_hashes[sha] = ak
            placed[ak] = rel
            plan.append(dict(parent=parent, att=att, src=src, dest=dest, rel=rel, sha=sha, size=size))

    review = review_manifest(manifest, index, deny_set, allow_set, trash_keys)

    if apply:
        for p in plan:
            if set(p["parent"]["data"]["collections"]) & deny_set:
                raise SyncAbort("internal consistency check failed immediately before copying")
        for p in plan:
            try:
                p["dest"].parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with open(p["src"], "rb") as s, open(p["dest"], "xb") as t:  # 'x' = never overwrite
                    for chunk in iter(lambda: s.read(1 << 20), b""):
                        digest.update(chunk)
                        t.write(chunk)
                    t.flush()
                    os.fsync(t.fileno())
                if digest.hexdigest() != p["sha"]:
                    raise OSError("copy does not match the source checksum; file left in place for inspection")
                rec = manifest_record(p["parent"], p["att"], names, p["src"], p["dest"], p["sha"], p["size"], settings, now)
                settings.manifest.parent.mkdir(parents=True, exist_ok=True)
                with open(settings.manifest, "a", encoding="utf-8", newline="\n") as mf:  # append-only
                    mf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    mf.flush()
                    os.fsync(mf.fileno())
                a["would_copy"] -= 1
                a["copied"] += 1
            except FileExistsError:
                a["would_copy"] -= 1
                a["conflict"] += 1
                placed[p["att"]["key"]] = None
                details.append(("conflict", p["att"]["key"], f"destination appeared during the run ({p['rel']}); skipped"))
            except OSError as exc:
                a["would_copy"] -= 1
                a["errors"] += 1
                placed[p["att"]["key"]] = None
                details.append(("error", p["att"]["key"], f"copy failed: {exc.__class__.__name__}"))

    # Index of eligible papers by Zotero collection. Denied items can never be in `eligible`.
    entries = build_index_entries(eligible, allow_set, cols, atts_by_parent, placed, settings)
    index_text = render_index(entries, now)
    if apply:
        index_status = write_index(settings.index, index_text)
    else:
        index_status = "would be regenerated on --apply"

    return dict(index_papers=len(eligible), index_status=index_status,now=now, apply=apply, counts=counts, att=a, plan=plan, details=details, review=review,
                warnings=warnings, groups=groups, crosscheck=(len(deny_set), crosscheck_n),
                allow_n=len(allow_set), deny_n=len(deny_set), deny_cfg=len(settings.deny),
                allow_cfg=len(settings.allow), parents=sum(1 for i in items if (i.get("data") or {}).get("itemType") not in NON_REGULAR and not (i.get("data") or {}).get("parentItem")),
                total_records=len(items), config_ok=True)


# ------------------------------------------------------------------- report

def render_report(r):
    c, a = r["counts"], r["att"]
    mode = "APPLY" if r["apply"] else "DRY RUN"
    dots = lambda label, n: f"  {label} {'.' * max(2, 34 - len(label))} {n}"
    lines = [
        f"ZOTERO SYNC - {mode}   {r['now'].strftime('%Y-%m-%d %H:%M')}",
        "Mode: files copied only with --apply" if not r["apply"] else "Mode: copies enabled; nothing is overwritten or deleted",
        f"Zotero API: OK (127.0.0.1)   personal library; group libraries visible: "
        f"{'unknown' if r['groups'] is None else r['groups']} (never scanned)",
        f"Collections: allow {r['allow_cfg']} configured ({r['allow_n']} incl. descendants); "
        f"deny {r['deny_cfg']} configured ({r['deny_n']} incl. descendants); config matches live Zotero: OK",
    ]
    lines += [f"WARNING: {w}" for w in r["warnings"]]
    lines += [f"Scanned: {r['parents']} parent items among {r['total_records']} records (annotations ignored)", "",
              "PARENT ITEMS",
              dots("Eligible", c["eligible"]),
              dots("Excluded: denied collections", c["excluded_denied"]) + f"   (also in an allowed collection: {c['excluded_denied_also_allowed']})",
              dots("Excluded: unfiled", c["unfiled"]),
              dots("Excluded: not on allowlist", c["not_allowlisted"]),
              dots("Excluded: in Zotero trash", c["trashed"]),
              dots("Excluded: group/unknown library", c["excluded_group"]),
              dots("Standalone attachments (unsupported)", c["standalone_attachments"]),
              f"Deny cross-check: PASS ({r['crosscheck'][0]} collections listed independently, "
              f"{r['crosscheck'][1]} member records agree with the exclusion)", "",
              "ATTACHMENTS (eligible parents only)",
              dots("Attachments examined", a["attachments"]),
              dots("Would copy" if not r["apply"] else "Copied", a["would_copy"] if not r["apply"] else a["copied"]),
              dots("Already imported (manifest)", a["already_imported"]),
              dots("Content duplicate (no copy)", a["content_duplicate"]),
              dots("Destination conflict (skipped)", a["conflict"]),
              dots("Changed in Zotero since import", a["changed_in_zotero"]),
              dots("Imported copy missing locally", a["imported_file_missing"]),
              dots("Local copy differs from manifest", a["local_file_differs"]),
              dots("Skipped: not a PDF", a["not_pdf"]),
              dots("Skipped: linked/not stored", a["not_stored"]),
              dots("Skipped: outside Zotero storage", a["outside_storage"]),
              dots("Unresolved (no path/file)", a["unresolved"]),
              dots("Skipped: attachment in trash", a["trashed"]),
              dots("Eligible items without attachment", a["no_attachment"]),
              dots("Orphan attachments", a["orphans"]),
              dots("Errors", a["errors"]), ""]
    if r["apply"] and r["plan"]:
        lines.append("COPIED")
    elif r["plan"]:
        lines.append("PLANNED COPIES (titles shown only for eligible items)")
    for p in r["plan"]:
        d = p["parent"]["data"]
        meta = " | ".join(str(x) for x in (year_of(p["parent"]) or "n.d.", first_author(p["parent"]) or "unknown author", d.get("title", "")))
        lines.append(f"  {p['att']['key']} -> {p['rel']}   ({meta})")
    if r["apply"] and a["copied"]:
        lines.append(f"  {a['copied']} file(s) copied; manifest updated")
    if r["details"]:
        lines += ["", "NOTES (keys and paths only)"] + [f"  [{s}] {k}: {t}" for s, k, t in r["details"]]
    if r["review"]:
        lines += ["", "PREVIOUSLY IMPORTED ITEMS WHOSE STATUS CHANGED (local files kept, nothing deleted)"]
        lines += [f"  item {ik} (attachment {ak}) {st}" for ak, ik, st in r["review"]]
    lines += ["", f"INDEX: refs/zotero-sync/index.md - {r['index_papers']} paper(s) listed by collection; {r['index_status']}"]
    lines += ["Safety: deny re-check on every planned copy PASS   Overwrites: none (only an unedited generated index is replaced)   Deletes: none"]
    lines.append("RESULT: nothing copied (dry run). Re-run with --apply to copy." if not r["apply"]
                 else f"RESULT: {a['copied']} copied, {a['errors']} errors.")
    return "\n".join(lines)


def save_report(settings, text, now):
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    for n in range(100):
        suffix = "" if n == 0 else f"-{n}"
        path = settings.reports_dir / f"zotero-sync_{now.strftime('%Y%m%d-%H%M%S')}{suffix}.txt"
        try:
            with open(path, "x", encoding="utf-8", newline="\n") as f:
                f.write(text + "\n")
            return path
        except FileExistsError:
            continue
    raise OSError("could not create a unique report file")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="zotero_sync.py",
        description="Copy eligible PDFs from Zotero (local API, read-only) into papers/zotero/. "
                    "Dry run by default; pass --apply to copy. Never overwrites or deletes files.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="plan only (default); writes nothing")
    mode.add_argument("--apply", action="store_true", help="copy eligible PDFs and update the manifest")
    p.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to the JSON config")
    args = p.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        settings = load_settings(args.config)
        client = ApiClient(settings.api_base, settings.timeout)
        result = run_sync(settings, client, apply=args.apply)
    except ZoteroUnavailable as exc:
        print(f"Zotero unavailable: {exc}\nNothing was copied.", file=sys.stderr)
        return EXIT_UNAVAILABLE
    except SyncAbort as exc:
        print(f"STOPPED (safety check): {exc}\nNothing was copied.", file=sys.stderr)
        return EXIT_ABORT
    text = render_report(result)
    print(text)
    if args.apply:
        try:
            print(f"\nReport saved: {save_report(settings, text, result['now']).relative_to(settings.root).as_posix()}")
        except OSError as exc:
            print(f"\nCould not save the report ({exc.__class__.__name__}); files were still processed.", file=sys.stderr)
    return EXIT_ERROR if result["att"]["errors"] else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
