---
description: Report-only review of this week's notes, matrix rows, and reading progress
argument-hint: (no arguments needed)
allowed-tools: Read, Glob, Grep, Bash(python:*), Bash(python3:*), Bash(py:*), Bash(ls:*), Bash(dir:*), WebSearch, WebFetch
---

Run my weekly research review. Extra context from me, if any: $ARGUMENTS

Follow `CLAUDE.md`: hard rules, verification protocol, writing style.

This command is report-only. Never edit, rewrite, delete, or update my notes or the matrix. Do not create files.

## Scope

Inspect notes in `notes/papers/` (ignore `.gitkeep`) and rows in `matrix/literature-matrix.csv`.

Focus on the current week. Use file modification times and the "Date read" field where available. State the exact date range you reviewed (use today's date from the environment). If dates are missing or ambiguous (for example copied files reset timestamps), say so rather than guessing. If there are no notes yet, say that plainly and stop after suggesting how to start.

## Return

### A. This week's activity
- Notes created or updated in the period.
- Relevant matrix rows.
- Discrepancies between notes and the matrix (missing rows, mismatched year or title, `note_file` pointing nowhere).

### B. Note quality
Flag thin notes that are missing any of: one-sentence claim, method, key evidence or results, limitations, my own explanation or critique, three takeaways written from memory. Separate fields that are missing (empty or still template prompts) from fields that are present but possibly inaccurate.

### C. Evidence and honesty checks
Flag:
- Claims stated more strongly than the paper supports.
- Unverified bibliographic details.
- Preprints described as established peer-reviewed results.
- Unsupported numerical claims.
- Conclusions that go beyond the evidence.
- Possible confusion between the authors' claims and my interpretations.

Point to the note section and the paper section, table, or figure I should check. Do not claim a note is inaccurate unless you have the paper's content; otherwise say what needs checking.

### D. Patterns across papers
Recurring topics, methods, evaluation metrics, assumptions, limitations, and disagreements in the matrix. If there are too few papers to see a pattern, say so. Do not invent patterns.

### E. Next week's reading recommendations
Suggest 2-4 candidate papers. For each: title and authors (if verified), year and venue (if verified), publication status, verification label, why it is a useful next step, and one question I should try to answer while reading it.

Use web search to verify candidates when available. Otherwise label them `FROM MEMORY` and say they need verification. Do not assume I have chosen a research topic; base suggestions on what my notes show, or on `reading-list/starter-list.md` if I have few notes.
