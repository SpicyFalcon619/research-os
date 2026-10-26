---
description: Add or update one literature-matrix row from an existing paper note
argument-hint: <note filename in notes/papers/>
allowed-tools: Read, Bash(python:*), Bash(python3:*), Bash(py:*)
---

Add or update the literature-matrix row for this note: $ARGUMENTS

Follow `CLAUDE.md`, especially the matrix rules. The matrix is `matrix/literature-matrix.csv`.

## Steps

1. If no argument was given, ask me which note. Look for `notes/papers/<argument>`. If the file does not exist, stop and tell me. Do not guess a different file.
2. Read the note. Take values only from what is explicitly written in it.
3. Build one row using exactly these columns, in this order:
   `key,year,title,venue,status,failure_or_topic,method,evidence,limitation,relevance,note_file`
4. Read and write the CSV with Python's standard-library `csv` module (UTF-8), not by hand-editing text. Write a short throwaway script or inline command; do not leave helper files in the workspace.
5. Check the `key` column for an existing row with the same key.
   - Exists: update that row only.
   - Does not exist: append a new row.
6. Preserve every other row and its values exactly, and keep the header unchanged.
7. Validate afterwards: the file parses, the header matches exactly, every row has 11 fields, and keys are unique. Report the resulting row.

## Rules

- Do not invent missing information. Leave unknown cells empty.
- Keep cells short and readable (a phrase, not a paragraph).
- `key`: derive from identifiers already in the note, such as the note filename without `.md`. Do not invent a DOI or other identifier.
- `year`, `title`, `venue`: copy from the note's bibliographic details; skip placeholders such as `[not provided]` and `[year not provided]` (leave the cell empty).
- `status`: use `skim`, `read`, `deep`, or `skip` only if the note explicitly states a valid value (for example under "Read level"). The template's unfilled "Skim / Read / Deep / Skip" is not a choice; leave the cell empty. Never guess. Never silently change an existing row's status. This field is reading progress, not publication status.
- `note_file`: the note's filename.
- `failure_or_topic`, `method`, `evidence`, `limitation`, `relevance`: summarize only what my note says, using my wording where possible. If the note's section is empty or still a template prompt, leave the cell empty.
- Do not modify the original note.

## Report

After updating, show the resulting row and list the cells that still need to be filled by me.
