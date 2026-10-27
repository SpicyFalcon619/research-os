# Working solo: using this workspace without an AI assistant

Everything in this workspace is plain files, a terminal, and Zotero. The slash commands (`/triage`, `/read-paper`, `/add-to-matrix`, `/find-related`, `/weekly-review`, `/sync-zotero`) need Claude Code, but each one has a manual equivalent below. Nothing here depends on an assistant.

Run terminal commands from the workspace folder (in VS Code: Terminal, then New Terminal; the prompt should show the folder).

## 1. Capture a paper

1. Open the paper's official page (publisher, proceedings, arXiv) in your browser with Zotero running.
2. Click the Zotero Connector button.
3. Check the title, authors, year, and venue against the paper itself. Fix mistakes by hand.
4. Put it in the `00 Inbox` collection and tag it `to-read`. Move it to `02 Reading Now` when you start, and to `03 Read and Noted` when your note is done.

## 2. Bring the PDF into the workspace (optional)

Zotero must be open, with Settings, Advanced, "Allow other applications on this computer to communicate with Zotero" ticked.

```
python scripts/zotero_sync.py            # dry run: prints the plan, writes nothing
python scripts/zotero_sync.py --apply    # copies the eligible PDFs
```

Problems:
- `Zotero refused the request (HTTP 403)`: the setting above is off.
- `Cannot reach Zotero`: Zotero is not running.
- `config file not found`: copy `scripts/zotero_sync_config.example.json` to `scripts/zotero_sync_config.local.json` and fill in your own collection keys and names.
- `STOPPED (safety check)`: read the message. It means something did not match what the config expects. Nothing was copied.

## 3. Read the paper (Keshav's three passes)

- **Pass 1, 5-10 minutes:** read the title, abstract, and introduction carefully; read the section headings only; read the conclusion; glance at the references. Then try the five Cs:
  - Category: what type of paper is it?
  - Context: which other papers is it related to?
  - Correctness: do the assumptions look valid?
  - Contributions: what does it claim?
  - Clarity: is it well written?
- **Pass 2, up to an hour:** look carefully at figures and tables (axes labeled? error bars?). Skip proofs. Mark references worth following. Stop when you can state the main idea and its supporting evidence.
- **Pass 3, hours:** re-create the work in your head: make the authors' assumptions and compare. Do this only for papers worth it.

You may stop after any pass. Stopping is a decision, not a failure.

This replaces `/triage` (do pass 1 yourself) and `/read-paper` (work through the sections, and write down what you understood before you look anything up).

## 4. Write the paper note

```
python scripts/new_note.py "Title" --authors "Smith et al." --year 2020 --venue "Venue" --url "https://doi.org/..."
```

This creates `notes/papers/YYYY-firstauthor-short-title.md` from the template, and never overwrites an existing note. Then:
- Fill each section in your own words. Short, imperfect sentences are fine.
- Write "not applicable" where a section does not fit.
- Keep what the authors say separate from what you think.
- Do not present anything as checked unless you checked it against the paper. Mark the rest as unverified.
- Write the three takeaways with the paper closed.

## 5. Add a row to the literature matrix

Open `matrix/literature-matrix.csv` in VS Code and add one line, with these 11 columns in this exact order:

```
key,year,title,venue,status,failure_or_topic,method,evidence,limitation,relevance,note_file
```

- `key`: the note's filename without `.md`.
- `status`: your reading progress, one of `skim`, `read`, `deep`, or `skip`. It is not publication status.
- Keep cells short. Leave unknown cells empty.
- Wrap a cell in double quotes if it contains a comma.
- Take values only from your own note.

Check the file afterwards:

```
python -c "import csv; r=list(csv.reader(open('matrix/literature-matrix.csv',encoding='utf-8'))); print(all(len(x)==11 for x in r), len(r)-1, 'rows')"
```

It should print `True` and the number of papers. This replaces `/add-to-matrix`.

## 6. Weekly review

Reread each note from the week and ask:
- Is any claim stated more strongly than the paper supports?
- Were the title, authors, year, and venue checked against the paper?
- Is a preprint described as peer-reviewed? An arXiv listing alone does not show peer review.
- Are any numbers unchecked?
- Does the note keep the authors' claims apart from your interpretation?
- Is every section filled in, including the three takeaways?

Then look across the matrix for repeated topics, methods, and limitations, and write down one question per paper. This replaces `/weekly-review`.

## 7. Find related papers

Open the paper's reference list (backward) and the "Cited by" link on Google Scholar or Semantic Scholar (forward). Prefer official proceedings and journal pages. A survey is a good start but can be outdated or biased. Citation counts help you find influential work; they do not show a paper is correct. This replaces `/find-related`.

## 8. Save to GitHub

```
git status
git add notes/papers/yourfile.md matrix/literature-matrix.csv
git commit -m "Add paper note for X"
git push
```

Run `git status` first and add files by name. Your PDFs, Zotero sync records, and local Zotero config are ignored by `.gitignore`, so they will not be committed.

## 9. If something breaks

- Run `python tests/test_zotero_sync.py` to check the sync script. It should end with `passed, 0 failed`.
- The README explains each part of the workspace, and `CLAUDE.md` holds the rules.
- You can paste `CLAUDE.md` into any AI chat as instructions. Treat what it says as a lead to check against the paper, never as the evidence itself.
