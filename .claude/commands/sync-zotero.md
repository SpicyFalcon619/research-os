---
description: Check Zotero for eligible PDFs and (after your approval) copy them into papers/zotero/
argument-hint: (no arguments; always starts with a dry run)
allowed-tools: Bash(python scripts/zotero_sync.py --dry-run), Bash(python scripts/zotero_sync.py)
---

Check Zotero for new research papers and report what a sync would do. Extra context from me, if any: $ARGUMENTS

Follow `CLAUDE.md`. Zotero is the source of truth; this workspace only receives copies. Typing `--apply` in the arguments is not approval to copy.

## Steps

1. Run the dry run: `python scripts/zotero_sync.py --dry-run`. It writes nothing. If `python` is not found, try `py scripts/zotero_sync.py --dry-run`.
2. Show me the summary exactly as printed. It is already free of titles and details for excluded items. Do not add, look up, or guess any detail about excluded items.
3. Explain in plain language what each non-zero line means (for example content duplicate, destination conflict, changed in Zotero) and which need a decision from me.
4. If the exit code is 3, Zotero is not reachable: tell me to open Zotero and enable Settings > Advanced > "Allow other applications on this computer to communicate with Zotero". Do not change Zotero settings yourself. If the exit code is 4, a safety check stopped the run: report the message and do not work around it (do not edit the config or the script to get past it).
5. Only if the dry run shows planned copies, ask me whether to apply. Run `python scripts/zotero_sync.py --apply` only after I say yes in this conversation, then show the result.

## Never

- Never move, rename, overwrite, or delete files, in the workspace or in Zotero. Never touch Zotero's database or data directory.
- Never edit `scripts/zotero_sync_config.local.json` or the manifest to change what is eligible, unless I ask. Never copy real collection keys or names into any tracked file.
- Never create notes, edit the literature matrix, or run `/triage` automatically. After an apply, you may suggest text such as `/triage papers/zotero/<item key>/<file>.pdf` for me to run myself.
- Imported items that later become ineligible or are trashed keep their local files. Report their status; do not remove them.
