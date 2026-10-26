---
description: Two-minute first-pass triage of a paper (no full summary)
argument-hint: <paper path or URL>
---

Do a quick Pass-1 triage (about two minutes of reading effort) of this paper: $ARGUMENTS

This is a shorter pre-screen modeled on the first pass of Keshav's three-pass method (Keshav himself budgets five to ten minutes for a human first pass). It does not replace my own first pass.

Follow `CLAUDE.md`: hard rules, verification protocol, writing style.

## Access

- If a path to a PDF or readable file is given, open and inspect it directly.
- If a URL is given, try to open the paper or a reliable source containing its content.
- If you cannot open it, say so and ask me for the PDF or accessible text. Do not guess the paper's contents from the title or from memory.
- If no argument was given, ask me which paper to triage.

## Look at

Title, abstract, introduction, section headings, figures and tables, conclusion, and the reference list at a glance. This is a skim, not a close read.

## Return

1. **Bibliographic details:** title, authors, year, venue, as available.
2. **Verification status:** which details you checked in the source you opened, and which are still unverified. A title seen in a search result is not verification.
3. **Publication status:** peer-reviewed publication, preprint, or other, with the evidence you saw (for example the proceedings page or a journal listing). An arXiv listing alone does not show peer review.
4. **One-sentence claim:** what the paper is trying to establish.
5. **Evidence type:** theoretical analysis, benchmark, experiment, observational study, human-subject study, survey, or other.
6. **Why it might matter to a beginner:** the potential learning value.
7. **Recommendation:** `skip`, `skim`, or `read`, with one line of reasoning. If it rests on general knowledge rather than a source you opened in this session, label it `FROM MEMORY`.
8. **Prerequisites:** up to three concepts I may need first.
9. **Confidence and uncertainty:** limits of this triage (for example, only the abstract was available, or evidence quality was not assessed).

## Constraints

- Do not write a full summary of the paper.
- Do not mark anything `VERIFIED` unless you opened the source and checked that specific item in this session.
- Do not edit my notes or the matrix. Triage is report-only.
