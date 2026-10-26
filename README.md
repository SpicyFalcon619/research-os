# Research Learning Workspace

## 1. Purpose

This is a general-purpose workspace for learning how to find, read, understand, organize, evaluate, and eventually write about academic papers. It is built for a Computer Science undergraduate interested in AI and Data Science who is new to research.

It is **not tied to any project, research question, thesis, or publication target.** You do not need to choose a topic to start. Claude Code acts as a mentor here, not a ghostwriter (see `CLAUDE.md`).

## 2. Directory map

| Path | What it is for |
| --- | --- |
| `CLAUDE.md` | Rules Claude follows here: mentor role, verification labels, naming, matrix format. |
| `.claude/commands/` | The five slash commands (section 8). |
| `notes/papers/` | Your notes on individual papers, in your own words. |
| `notes/templates/paper-note.md` | The template new notes are made from. |
| `matrix/literature-matrix.csv` | A table for comparing papers. It starts with only a header row. |
| `reading-list/starter-list.md` | A staged starter list, a four-week plan, and a guide to finding papers. |
| `refs/` | Bibliography exports (optional, see section 6). |
| `papers/` | Local PDF storage. PDFs here are not committed to Git. |
| `projects/` | Empty on purpose. Use it only when you choose to start a project. |
| `scripts/new_note.py` | Creates a new paper note from the template. |
| `.gitignore` | Keeps PDFs, secrets, and Python junk out of Git. |

The **literature matrix is a comparison tool, not a replacement for detailed notes.** Its cells are short. The thinking lives in your notes.

## 3. Initial setup

You do not need Zotero installed already. Zotero is free reference-management software that saves papers and their citation details, and stores your PDFs and annotations.

1. **Install Zotero.** Download the current stable Zotero desktop app from <https://www.zotero.org/download/> and run the installer.
2. **Install the Zotero Connector** for your browser from the same page (<https://www.zotero.org/download/>). It adds a toolbar button that saves the paper you are viewing. Keep the Zotero app open while saving.
3. **Save a paper.** Open a paper's page (publisher, arXiv, ACL Anthology) and click the Connector button. Saving from the publisher or proceedings page gives better metadata than saving from a search result.
4. **Verify the metadata.** Compare the item in Zotero (title, authors, year, venue, DOI) with the paper itself. Fix errors by hand. Automatic capture is often wrong, especially for preprints that were later published.
5. **Attach and annotate the PDF.** Zotero often attaches an open-access PDF automatically. If not, use "Add Attachment". Double-click the PDF to open Zotero's reader, then highlight and add comments. Annotations are saved in your Zotero library.
6. **Create the collections** in section 4.
7. **Keep local backups** of important PDFs and notes (see section 13). Zotero's own file storage is not a backup plan.

## 4. Zotero collections

Create these top-level collections (right-click "My Library", then "New Collection"):

- `00 Inbox`: everything new lands here first.
- `01 Foundations`: papers you keep returning to.
- `02 Reading Now`: the one to three papers you are working through this week.
- `03 Read and Noted`: papers you have read and written notes on.

Collections are organizational **views**. A paper can belong to more than one collection, and removing it from a collection does not delete it from your library.

## 5. Zotero tags

Recommended tags: `to-read`, `skimmed`, `deep-read`, `survey`, `foundational`.

A **collection** answers "where is this in my workflow?" A **tag** describes the paper itself or how far you got with it, and works across collections. Example: a paper in `01 Foundations` can be tagged `survey` and `skimmed`.

Tags in Zotero are separate from the `status` column in the matrix. The matrix `status` (`skim`, `read`, `deep`, `skip`) is your reading progress, which you set yourself.

## 6. Optional: Better BibTeX integration

This is only useful if you eventually write papers in LaTeX or Overleaf. **Skip it for now** if that does not apply.

If you decide to use it:

1. Follow the official installation page, <https://retorque.re/zotero-better-bibtex/installation/>. It links the latest `.xpi` release on GitHub. In Firefox, right-click and save the file instead of clicking it.
2. In Zotero: Tools, then Plugins, then the gear icon, then "Install Plugin From File...", and select the `.xpi`.
3. Right-click your library or a collection, choose "Export...", format "Better BibTeX", and tick **Keep updated** so the file refreshes as your library changes. Save it as `refs/library.bib` in this workspace. (Steps 1-2 are from the official page. The export option name in step 3 is from my memory of the add-on, so check its documentation if the dialog looks different.)

Nothing in this workspace installs Better BibTeX, changes Zotero settings, or creates the export for you.

## 7. The reading routine

1. **Capture** the paper in Zotero (`00 Inbox`).
2. **Check the bibliographic details** against the paper or the official page.
3. **Triage** it: `/triage`, or do your own quick look at the title, abstract, headings, figures, and conclusion.
4. **Read** with Keshav's three-pass method:
   - Pass 1: a quick scan (the paper says five to ten minutes) to see what the paper is and whether to continue.
   - Pass 2: read carefully, skipping proofs and fine details, to grasp the content.
   - Pass 3: dig in, re-deriving or "re-implementing" the paper in your head, to understand it deeply.
5. **Write a note** in your own words with `python scripts/new_note.py`.
6. **Add or update the matrix** row (`/add-to-matrix`).
7. **Follow citations** backward (what it cites) and forward (what cites it): `/find-related`.
8. **Review weekly:** `/weekly-review`.

Not every paper deserves a deep read. Stopping after Pass 1 is a legitimate outcome and a skill in itself.

## 8. How to use the slash commands

Run these inside Claude Code started in this folder. They require Claude Code to be open in this workspace. Commands that look at papers need either a readable file path or a URL Claude can open. If it cannot open the paper, it will ask you for the PDF or text instead of guessing.

| Command | What it does | Example |
| --- | --- | --- |
| `/triage <paper path or URL>` | Quick first-pass assessment. Returns details, verification status, a one-sentence claim, evidence type, `skip`/`skim`/`read`, prerequisites, and uncertainty. | `/triage papers/my-paper.pdf` |
| `/read-paper <paper path or URL>` | A tutoring session, one section at a time. It asks what you understand before explaining. | `/read-paper https://arxiv.org/abs/1706.03762` |
| `/add-to-matrix <note filename>` | Adds or updates one matrix row from a note in `notes/papers/`, using only what is in the note. Empty cells are left empty and reported. | `/add-to-matrix 2017-vaswani-attention-is-all-you-need.md` |
| `/find-related <paper, URL, title, or topic>` | Suggests candidate papers by citation chaining and search, each labeled by verification. It discovers only; it does not save anything. | `/find-related "Attention Is All You Need"` |
| `/weekly-review` | Report on this week's notes and matrix rows, quality, honesty checks, patterns, and 2-4 suggestions. Report-only: it never edits your files. | `/weekly-review` |

Limitations:

- `/triage` and `/read-paper` can only check what they can open. Paywalled pages often block them, so a PDF path works best.
- `/find-related` needs web access. Search results are leads. The command labels each candidate, and you should open the sources yourself.
- `/add-to-matrix` needs the note filename to exist in `notes/papers/`, and it needs Python.
- `/weekly-review` works best when notes have a "Date read" or recent file dates.

## 9. How to create a new note

```
python scripts/new_note.py "Paper Title" --authors "Vaswani et al." --year 2017 --venue NeurIPS --url "https://example.com/paper"
```

- `"Paper Title"` is required. Quote it.
- `--authors`, `--year`, `--venue`, `--url` are optional. Use only details you have checked.
- `--first-author` is an optional override for the author name used in the filename.
- The note is saved in `notes/papers/` as `YYYY-firstauthor-short-title.md` and the path is printed.
- The year must be a four-digit year between 1900 and next year. If you give none, the filename uses `nd` and the note shows `[year not provided]`. The script never guesses the year.
- Missing details are shown as `[not provided]` so you can fill them in.
- **If the file already exists, the script stops with an error and leaves it untouched.** It never overwrites a note.
- Run `python scripts/new_note.py --help` for usage. On Windows, `py scripts/new_note.py ...` also works.

## 10. Research honesty

- Never cite a paper you have not opened.
- Verify that a source supports the statement you cite it for.
- Treat AI summaries as leads, not authoritative evidence.
- Distinguish preprints from peer-reviewed publications.
- Do not equate citation count with quality.
- Keep uncertainty visible.
- Do not invent results or research gaps.
- Write your own interpretation before asking AI to polish it.

Claude labels research recommendations `VERIFIED`, `FROM MEMORY`, `UNVERIFIED`, or `COULD NOT VERIFY` (definitions in `CLAUDE.md`). Treat anything not marked `VERIFIED` as a lead to check.

## 11. This week's starter plan (about 2-4 hours)

You do not need to choose a topic.

1. **Install Zotero and the Connector** (section 3). About 20-30 minutes.
2. **Look around the workspace** and test the script. Open `reading-list/starter-list.md`. Run `python scripts/new_note.py --help`.
3. **Read Keshav's paper** (Entry 1 in the reading list). It is only a few pages. Save it in Zotero first and check its metadata.
4. **Create one paper note in your own words.** Use the script for Keshav's paper, then fill in the template. Write the three takeaways without looking at the paper.
5. **Practice the matrix.** Run `/add-to-matrix <your note filename>` and look at which cells it leaves empty. Fill in your reading status yourself if you want it recorded.
6. **Review the reading list** and pick one foundational paper for next week (the Nature overview, or Dropout, are the suggestions in the list).

## 12. Syncing PDFs from Zotero (optional)

`python scripts/zotero_sync.py` copies PDFs from Zotero into `papers/zotero/<item key>/`. Zotero stays the source of truth: the script only reads from it and never moves, changes, or deletes anything there.

**Setup (once):**
1. Keep Zotero open. In Zotero: Settings, Advanced, tick "Allow other applications on this computer to communicate with Zotero". This lets programs on your PC read your library through `127.0.0.1`; you can untick it between syncs.
2. Copy `scripts/zotero_sync_config.example.json` to `scripts/zotero_sync_config.local.json` and replace the placeholders with your own collection keys and names. List the collections that may be imported, and any collection that must always be excluded. The local file is git-ignored, so your real collection names never reach Git. The script stops if Zotero no longer matches the config (for example a collection was renamed).

**Use:**
- `python scripts/zotero_sync.py` runs a **dry run**: it prints what would happen and writes nothing. In Claude Code, `/sync-zotero` does the same and asks before copying.
- `python scripts/zotero_sync.py --apply` copies the eligible PDFs. Each is recorded in `refs/zotero-sync/manifest.jsonl` (one line per attachment, appended only) and a report is saved in `refs/zotero-sync/reports/`. It also regenerates `refs/zotero-sync/index.md`, a list of your papers by Zotero collection with the location of each PDF here. Do not edit that file by hand: a hand-edited copy is never overwritten, and the index is not updated until you move it aside.
- Everything under `refs/zotero-sync/` and `papers/zotero/` is git-ignored, because it lists your personal library.

**Rules it follows:**
- Only the configured allowed collections (and their subcollections) are eligible. Anything in an excluded collection or its subcollections is excluded, even if the item is also in an allowed collection. Unfiled items, trashed items, and group libraries are skipped.
- Duplicates are found by Zotero's item and attachment keys and by file checksum (SHA-256), never by title. An identical PDF already in `papers/` (for example one you added by hand) is reported and not copied again.
- Existing files are never overwritten. If a destination exists with different content, it is reported as a conflict and skipped.
- If an imported paper later leaves an allowed collection or is trashed, your local copy stays and the report mentions it.
- It does not write notes, change the literature matrix, or triage papers.
- If anything is unclear (missing collection, incomplete response), it stops before copying anything. Exit code 3 means Zotero was unreachable; 4 means a safety check stopped it.

## 13. Backups and maintenance

- **In Git** (if you use it for this folder): `README.md`, `CLAUDE.md`, the commands, scripts, notes, templates, the matrix, the reading list, and the tests.
- **Excluded by `.gitignore`:** `papers/*.pdf`, `papers/zotero/`, `refs/zotero-sync/`, `scripts/zotero_sync_config.local.json`, `.env`, `.claude/settings.local.json`, Python caches and virtual environments, and `.DS_Store`.
- **Ignoring is not backing up.** `.gitignore` stops accidental commits of PDFs; it does not copy them anywhere. Keep a separate backup of PDFs and of your Zotero library (cloud storage or an external drive).
- **Back up your notes.** They are your own work and the main product of this workspace. If this folder is a Git repository, commit regularly and push to a remote.
- `.gitignore` does not remove files Git already tracks. If you committed a PDF earlier, it stays in history until you remove it deliberately.
- Never store secrets, API keys, or passwords in this folder.
