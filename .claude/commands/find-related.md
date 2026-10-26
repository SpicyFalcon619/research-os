---
description: Find related literature by citation chaining and targeted searches
argument-hint: <paper path, URL, title, or research topic>
---

Find literature related to: $ARGUMENTS

Follow `CLAUDE.md`: hard rules, verification protocol, writing style. Use web search and source inspection (WebSearch, WebFetch). If they are unavailable, say so and label everything `FROM MEMORY`. If no argument was given, ask what to start from.

## What to find

**If a seed paper is given** (path, URL, or title):
- 3-5 backward references: earlier papers the seed paper cites.
- 3-5 newer citing papers: later works that cite the seed paper.
- 1-2 relevant survey or review papers.

**If a topic is given:** first find a suitable starting paper or survey, then chain citations from it where possible.

## For each candidate give

1. Title
2. Authors
3. Year
4. Venue, if available
5. Publication status: peer-reviewed, preprint, or other (an arXiv listing alone does not show peer review)
6. A direct source link you actually opened
7. Verification label: `VERIFIED`, `FROM MEMORY`, `UNVERIFIED`, or `COULD NOT VERIFY`
8. Why it may be worth reading
9. Prerequisites or caveats

## Discovery rules

- Prefer official proceedings, journal sites, publisher pages, and the primary paper.
- Use Semantic Scholar, Google Scholar, and other academic indexes to discover candidates, then check the source.
- Distinguish papers that cite the seed paper from papers that are merely related. If you could not verify a citation relationship, say so.
- Prefer recent work when recency matters, but keep older foundational work.
- Include surveys when they help a beginner, and note that surveys can be outdated, incomplete, or biased.
- Do not call a search result `VERIFIED` unless you opened the source and checked the details you list.
- Never fill in missing metadata or findings from memory without labeling them `FROM MEMORY`.
- Do not claim the list is exhaustive.
- Do not claim a research gap because a search found nothing.
- Citation counts may help discovery but say nothing about correctness.

## Constraints

This command only discovers candidates. Do not download papers. Do not create or modify files, notes, or the matrix.
