# Starter Reading List

A general-purpose list for learning how research works and for getting oriented in machine learning, NLP, and human-AI interaction. It assumes no research project and no chosen specialization. It is not exhaustive, and no paper here is mandatory.

## How to read the labels

Checked on **2026-10-26**.

| Label | Meaning |
| --- | --- |
| `✓ VERIFIED` | A relevant source was opened and the listed metadata was checked in that session. |
| `FROM MEMORY` | Remembered, not checked. |
| `UNVERIFIED` | Verification incomplete. |
| `COULD NOT VERIFY` | Verification attempted but failed or was inconclusive. |

Important limits on what "verified" means here:

- The label covers **bibliographic details, publication status, and links** only. It does not mean I read the full paper or checked its results.
- Each entry has a **Scope checked** line saying exactly what was opened. Where an official publisher page blocked access, the entry says what was used instead.
- The "Why read" and "Learn" text is general-knowledge guidance written to help you choose. It is not a verified summary. Read the paper yourself and check it.
- Peer-review status: pages for NeurIPS, ICLR, ACL, FAccT, IUI, CVPR, JMLR and Nature show a publication venue. They do not describe the review process. That these venues are peer-reviewed is general knowledge (`FROM MEMORY`).
- An arXiv listing alone does not establish peer review. Where a paper is both a preprint and a published version, both are listed, and they can differ.

## Reading order and difficulty

Go through the four stages roughly in order, but you do not need to finish a stage first. Each entry says whether it suits you now or later. Difficulty ratings are my judgment (`FROM MEMORY`), not verified.

1. **Stage 1: Research methodology.** Start here. Short and non-technical.
2. **Stage 2: ML and deep learning foundations.** Begin with the Nature overview. Adam, Dropout, and ResNet need some calculus and linear algebra. Treat them as a second pass.
3. **Stage 3: Transformers and modern NLP.** "Attention Is All You Need" is the anchor. The others build on it and are more technical. BERT, GPT-3, and InstructGPT are long, so skim them first and read selected sections.
4. **Stage 4: Empirical research and human-AI interaction.** Suitable early, because user studies need little math. They are the best place to learn study design, measurement, and the correlation vs. causation distinction.

| Suitable as a beginner | Later, more technical stage |
| --- | --- |
| Keshav; LeCun et al.; Kim et al.; Kulesza et al.; Sharma et al. (skim first) | Adam; Dropout; ResNet; Vaswani et al.; Devlin et al.; Brown et al.; Wei et al.; Ouyang et al. |

---

## Stage 1: Research methodology and paper reading

### 1. How to Read a Paper (Keshav)

- **Label:** ✓ VERIFIED (bibliographic details; first page of an open copy)
- **Authors:** S. Keshav
- **Year / venue:** 2007, ACM SIGCOMM Computer Communication Review, vol. 37, no. 3, pp. 83-84
- **Type:** Short methodology article (guide), not original experimental research
- **Publication status:** Published journal article. Whether this piece was peer-reviewed was not established by the sources I opened.
- **Links:** Official: <https://doi.org/10.1145/1273445.1273458> (the ACM page itself returned HTTP 403 to me). Open copy: <https://6826.csail.mit.edu/2020/papers/howtoread.pdf> (a course-hosted copy, not the author's own page).
- **Scope checked:** Crossref DOI record (title, author, journal, volume, issue, pages, date); first page of the open copy (title, author, abstract, the first-pass steps, journal footer "Volume 37, Number 3, July 2007"). I did not read pages 2-4.
- **Why read:** It teaches the three-pass method that the rest of this workspace is built around.
- **Learn:** What each pass is for, the "five Cs" checklist, and when to stop reading.
- **Prerequisites:** None.

---

## Stage 2: Machine learning and deep learning foundations

### 2. Deep learning (LeCun, Bengio, Hinton)

- **Label:** ✓ VERIFIED (bibliographic details via DOI registry only)
- **Authors:** Yann LeCun, Yoshua Bengio, Geoffrey Hinton
- **Year / venue:** 2015, Nature, vol. 521, issue 7553, pp. 436-444
- **Type:** Survey/review-style overview, not an original experiment (`FROM MEMORY`; the record I checked only says "journal article")
- **Publication status:** Published in a journal (Nature). Peer review not described in the source I opened.
- **Links:** Official: <https://doi.org/10.1038/nature14539>. Open version: none verified.
- **Scope checked:** Crossref DOI record (authors, title, journal, volume, issue, pages, online date 27 May 2015, DOI). The Nature page redirected to a login handshake and was not opened. Abstract and full text not read.
- **Why read:** A broad, readable overview of what deep learning is and how it is trained.
- **Learn:** Core vocabulary (layers, backpropagation, representation learning) and how the field described itself in 2015.
- **Prerequisites:** Basic programming; some linear algebra helps.
- **Caveat:** Written in 2015. Later developments (such as Transformers) are not covered.

### 3. Adam: A Method for Stochastic Optimization (Kingma, Ba)

- **Label:** ✓ VERIFIED (arXiv page and ICLR announcement; proceedings page not opened)
- **Authors:** Diederik P. Kingma, Jimmy Ba
- **Year / venue:** arXiv first posted 22 Dec 2014 (latest version v9, 30 Jan 2017); ICLR 2015
- **Type:** Original research (method with theory and experiments)
- **Publication status:** arXiv preprint, also published at ICLR 2015. The ICLR venue comes from the authors' arXiv comment ("Published as a conference paper at the 3rd International Conference for Learning Representations, San Diego, 2015") and the ICLR blog's 2015 Test of Time announcement. I did not open the ICLR proceedings page. The arXiv v9 may differ from the 2015 proceedings version.
- **Links:** Preprint (open): <https://arxiv.org/abs/1412.6980>. Official proceedings page: not opened. ICLR announcement: <https://blog.iclr.cc/2025/04/14/announcing-the-test-of-time-award-winners-from-iclr-2015/>
- **Scope checked:** arXiv abstract page (title, authors, versions, comment line); ICLR blog page mentions the paper. No full text.
- **Why read:** Adam is among the most commonly used optimizers in deep learning, and the paper shows how a method paper is organized.
- **Learn:** What an optimizer does, learning rate, momentum-style moving averages, and how to read an algorithm box.
- **Prerequisites:** Gradient descent; basic calculus. Do this one in the later stage.

### 4. Dropout: A Simple Way to Prevent Neural Networks from Overfitting (Srivastava et al.)

- **Label:** ✓ VERIFIED
- **Authors:** Nitish Srivastava, Geoffrey Hinton, Alex Krizhevsky, Ilya Sutskever, Ruslan Salakhutdinov
- **Year / venue:** 2014, Journal of Machine Learning Research, vol. 15(56), pp. 1929-1958
- **Type:** Original research
- **Publication status:** Published journal article (JMLR). Review process not described on the page I opened.
- **Links:** Official and open: <https://jmlr.org/papers/v15/srivastava14a.html> (PDF: <https://www.jmlr.org/papers/volume15/srivastava14a/srivastava14a.pdf>)
- **Scope checked:** JMLR paper page (title, authors, journal, volume, pages, year, PDF link). Full text not read.
- **Why read:** Introduces a widely used regularization technique with extensive experiments, so it is a good example of how to evaluate empirical claims.
- **Learn:** Overfitting, regularization, and how authors compare against baselines across datasets.
- **Prerequisites:** Neural network basics; overfitting.
- **Caveat:** The "Simple" in the title does not make it a light read, so read selectively.

### 5. Deep Residual Learning for Image Recognition (He et al.)

- **Label:** ✓ VERIFIED (arXiv page and DOI registry record; CVF and IEEE pages not opened)
- **Authors:** Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
- **Year / venue:** arXiv Dec 2015 (comment: "Tech report"); CVPR 2016, pp. 770-778, IEEE
- **Type:** Original research
- **Publication status:** arXiv preprint, and a CVPR 2016 conference paper per the DOI record. Preprint and proceedings versions may differ.
- **Links:** Official: <https://doi.org/10.1109/CVPR.2016.90>. Open: <https://arxiv.org/abs/1512.03385>. (The CVF open-access page returned HTTP 403.)
- **Scope checked:** arXiv abstract page (title, authors, submission date 10 Dec 2015, comment); Crossref DOI record (authors, title, proceedings, pages, June 2016). Full text not read.
- **Why read:** Residual connections are a standard building block, and the same idea appears inside Transformers.
- **Learn:** Why very deep networks were hard to train and what a skip connection changes.
- **Prerequisites:** Convolutional networks; training basics. Do this one in the later stage.

---

## Stage 3: Transformers and modern NLP

### 6. Attention Is All You Need (Vaswani et al.)

- **Label:** ✓ VERIFIED
- **Authors:** Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin
- **Year / venue:** 2017, Advances in Neural Information Processing Systems 30 (NIPS 2017). arXiv v1 12 Jun 2017.
- **Type:** Original research
- **Publication status:** Conference proceedings paper (NeurIPS/NIPS 2017) and arXiv preprint. Proceedings and arXiv v7 (last revised 2 Aug 2023) may differ.
- **Links:** Official: <https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html>. Open: <https://arxiv.org/abs/1706.03762>
- **Scope checked:** NeurIPS proceedings page and arXiv abstract page (title, authors, venue, dates). Full text not read.
- **Why read:** It introduced the Transformer architecture used by most modern language models.
- **Learn:** Attention, self-attention, encoder-decoder structure, and how to read an architecture figure.
- **Prerequisites:** Neural networks, matrix multiplication, sequence models (RNNs) at a high level. This is the Week 2 paper.

### 7. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding (Devlin et al.)

- **Label:** ✓ VERIFIED
- **Authors:** Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova
- **Year / venue:** NAACL-HLT 2019 (Proceedings of the 2019 Conference of the North American Chapter of the ACL: Human Language Technologies, Volume 1), June 2019, pp. 4171-4186. DOI 10.18653/v1/N19-1423. arXiv v1 11 Oct 2018.
- **Type:** Original research
- **Publication status:** Conference proceedings paper (ACL Anthology) and arXiv preprint (v2 last revised 24 May 2019).
- **Links:** Official: <https://aclanthology.org/N19-1423/>. Open: <https://arxiv.org/abs/1810.04805>
- **Scope checked:** ACL Anthology page and arXiv abstract page (title, authors, venue, pages, DOI, dates). Full text not read.
- **Why read:** A landmark example of pre-training followed by fine-tuning.
- **Learn:** Pre-training vs. fine-tuning, masked language modeling, and benchmark-style evaluation.
- **Prerequisites:** The Transformer paper.

### 8. Language Models are Few-Shot Learners (Brown et al.), "GPT-3"

- **Label:** ✓ VERIFIED
- **Authors:** Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah and 27 others (31 authors in total on the arXiv page; see source for the full list)
- **Year / venue:** NeurIPS 2020 (Advances in Neural Information Processing Systems 33). arXiv submitted 28 May 2020.
- **Type:** Original research (large empirical evaluation)
- **Publication status:** Conference proceedings paper and arXiv preprint.
- **Links:** Official: <https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html>. Open: <https://arxiv.org/abs/2005.14165>
- **Scope checked:** NeurIPS proceedings page and arXiv abstract page (title, authors, venue, date, "40+32 pages"). Full text not read.
- **Why read:** Shows in-context (few-shot) learning at scale and how a very large evaluation is reported.
- **Learn:** Zero-shot vs. few-shot prompting, how scale is argued to matter, and how to treat benchmark results critically.
- **Prerequisites:** Transformer and language-modeling basics. Long, so skim first.

### 9. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (Wei et al.)

- **Label:** ✓ VERIFIED
- **Authors:** Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, Denny Zhou
- **Year / venue:** NeurIPS 2022 (Advances in Neural Information Processing Systems 35, Main Conference Track). arXiv v1 28 Jan 2022; v6 10 Jan 2023.
- **Type:** Original research
- **Publication status:** Conference proceedings paper and arXiv preprint.
- **Links:** Official: <https://proceedings.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html>. Open: <https://arxiv.org/abs/2201.11903>
- **Scope checked:** NeurIPS proceedings page and arXiv abstract page (title, authors, venue, dates). Full text not read.
- **Why read:** A compact paper about prompting, good for practicing "what does the evidence actually show."
- **Learn:** Prompt-based evaluation, and how to ask whether a "reasoning" claim is supported by the tasks used.
- **Prerequisites:** What a large language model is; prompting basics.

### 10. Training Language Models to Follow Instructions with Human Feedback (Ouyang et al.), "InstructGPT"

- **Label:** ✓ VERIFIED
- **Authors:** Long Ouyang, Jeff Wu, Xu Jiang, Diogo Almeida and 16 others (20 authors in total; see source for the full list)
- **Year / venue:** NeurIPS 2022 (Advances in Neural Information Processing Systems 35, Main Conference Track). arXiv submitted 4 Mar 2022.
- **Type:** Original research
- **Publication status:** Conference proceedings paper and arXiv preprint.
- **Links:** Official: <https://proceedings.neurips.cc/paper_files/paper/2022/hash/b1efde53be364a73914f58805a001731-Abstract-Conference.html>. Open: <https://arxiv.org/abs/2203.02155>
- **Scope checked:** NeurIPS proceedings page and arXiv abstract page (title, authors, venue, date). Full text not read.
- **Why read:** Describes human-feedback training of language models, which connects Stage 3 to the human-AI questions in Stage 4.
- **Learn:** What reinforcement learning from human feedback (RLHF) is trying to do and how human labelers and preferences enter the pipeline.
- **Prerequisites:** Language-model basics; the idea of reward and policy from reinforcement learning helps.

---

## Stage 4: Empirical research and human-AI interaction

### 11. Towards Understanding Sycophancy in Language Models (Sharma et al.)

- **Label:** ✓ VERIFIED
- **Authors:** Mrinank Sharma, Meg Tong, Tomek Korbak, David Duvenaud, Amanda Askell, Sam Bowman, Esin Durmus, Zac Hatfield-Dodds, Scott Johnston, Shauna Kravec, Timothy Maxwell, Sam McCandlish, Kamal Ndousse, Oliver Rausch, Nicholas Schiefer, Da Yan, Miranda Zhang, Ethan Perez (ICLR proceedings spelling)
- **Year / venue:** ICLR 2024 (poster). arXiv v1 20 Oct 2023; v4 10 May 2025.
- **Type:** Original research (empirical evaluation of models plus analysis of human preference data)
- **Publication status:** Conference paper (ICLR 2024) and arXiv preprint. The arXiv v4 may differ from the conference version.
- **Discrepancy noted:** Some names differ between sources: arXiv shows "Tomasz Korbak", "Samuel R. Bowman", "Scott R. Johnston"; the ICLR proceedings show "Tomek Korbak", "Sam Bowman", "Scott Johnston". They appear to be name variants, but I did not investigate further.
- **Links:** Official: <https://proceedings.iclr.cc/paper_files/paper/2024/hash/0105f7972202c1d4fb817da9f21a9663-Abstract-Conference.html>. Open: <https://arxiv.org/abs/2310.13548>. (OpenReview returned a browser-check page and was not opened.)
- **Scope checked:** ICLR proceedings page, ICLR virtual-site page (event type: Poster), and arXiv abstract page (title, authors, dates, comment). Abstract-level descriptions only. Full text not read.
- **Why read:** A recent paper on a behavior of RLHF-trained assistants, useful for seeing how model behavior is measured and how causes are argued.
- **Learn:** How authors test for a behavior across several systems, and the difference between showing a behavior exists and explaining why it happens.
- **Prerequisites:** InstructGPT / RLHF idea at a high level.

### 12. "I'm Not Sure, But...": Examining the Impact of Large Language Models' Uncertainty Expression on User Reliance and Trust (Kim et al.)

- **Label:** ✓ VERIFIED
- **Authors:** Sunnie S. Y. Kim, Q. Vera Liao, Mihaela Vorvoreanu, Stephanie Ballard, Jennifer Wortman Vaughan
- **Year / venue:** FAccT 2024 (The 2024 ACM Conference on Fairness, Accountability, and Transparency), 3-6 June 2024, Rio de Janeiro, pp. 822-835. DOI 10.1145/3630106.3658941. arXiv v1 1 May 2024; v2 15 May 2024.
- **Type:** Original research (human-subject experiment; the abstract states a pre-registered study with N=404)
- **Publication status:** Conference proceedings paper (arXiv comment: "Accepted to FAccT 2024") and arXiv preprint (v2 includes the appendix).
- **Links:** Official: <https://doi.org/10.1145/3630106.3658941>. Open: <https://arxiv.org/abs/2405.00623> and the conference-hosted PDF <https://facctconference.org/static/papers24/facct24-56.pdf>
- **Scope checked:** First page of the FAccT PDF (title, authors, abstract, ACM reference format, DOI); Crossref DOI record (pages, date); arXiv abstract page. The rest of the paper was not read, so study design details beyond the abstract are not verified.
- **Why read:** A concrete example of a human-subject experiment on trust and reliance in AI systems. Your Week 3 candidate.
- **Learn:** Research question, experimental conditions, participants, measures (reliance, trust, accuracy), and what an experiment can and cannot say about cause.
- **Prerequisites:** None beyond basic statistics vocabulary (significance, sample size). Concepts like "overreliance" are explained in the paper.
- **Note:** You described this as "research on LLM uncertainty expression and user reliance or trust." The exact title and authors above come from the paper's first page.

### 13. Principles of Explanatory Debugging to Personalize Interactive Machine Learning (Kulesza et al.)

- **Label:** ✓ VERIFIED (bibliographic details via DOI registry only)
- **Authors:** Todd Kulesza, Margaret Burnett, Weng-Keen Wong, Simone Stumpf
- **Year / venue:** 2015, Proceedings of the 20th International Conference on Intelligent User Interfaces (IUI '15), pp. 126-137, ACM. DOI 10.1145/2678025.2701399
- **Type:** Not checked. The record says "proceedings article"; I did not read the abstract. Your list says "IUI 2015", which matches.
- **Publication status:** Conference proceedings paper. Peer review not described in the source I opened.
- **Title note:** The full title in the record is "Principles of Explanatory Debugging to Personalize Interactive Machine Learning". The shorter form "Principles of Explanatory Debugging" appears to be an abbreviation.
- **Links:** Official: <https://doi.org/10.1145/2678025.2701399> (the ACM page itself was not opened). Open version: none verified.
- **Scope checked:** Crossref DOI record only (title, authors, proceedings, pages, date, publisher, DOI). The abstract and full text were not opened. What the paper's study is, and its findings, are `UNVERIFIED`.
- **Why read:** `FROM MEMORY`: it is an influential human-computer interaction paper on how people can understand and correct a machine learning system. Check the abstract before relying on this.
- **Learn:** To be decided after you read the abstract.
- **Prerequisites:** Basic familiarity with machine learning; some HCI vocabulary.

---

## Four-week starter plan

You do not need to pick a permanent specialization during these four weeks. Adjust the pace to your schedule.

### Week 1: Learn how to read research

- Read Keshav's paper (Entry 1).
- Read one foundational paper. Suggestion: the Nature overview (Entry 2). It is a broad introduction. Dropout (Entry 4) is an alternative if you want an original research paper.
- Practice: write a one-sentence summary and list what evidence the authors give. Use `python scripts/new_note.py`, then compare your note with the paper.

### Week 2: Understand a major architecture

- Read "Attention Is All You Need" (Entry 6).
- Learn the basic idea of attention and the Transformer.
- Identify the problem, method, evidence, and limitations. Try `/read-paper` for a guided session.

### Week 3: Learn empirical research

- Read a human-AI interaction user study. Suggestion: Kim et al. (Entry 12).
- Identify the research question, study design, participants, measurements, results, and limitations.
- Practice distinguishing correlation from causation where relevant. Ask: did the researchers assign the conditions (an experiment), or only observe them?

### Week 4: Explore an area of personal interest

- Pick an AI or Data Science topic that genuinely interests you.
- Find a relevant survey or review paper on it.
- Identify five additional papers through backward and forward citation chaining. Try `/find-related`.
- Record why each might be worth reading, and check each against the source before trusting it.

---

## Where to find more papers

| Tool | Good for | Watch out for |
| --- | --- | --- |
| [Google Scholar](https://scholar.google.com) | Broad search across fields; "Cited by" for forward chaining | Mixes preprints, theses, and low-quality sources; citation counts vary. |
| [Semantic Scholar](https://www.semanticscholar.org) | Citations and references lists, related-paper suggestions | Coverage and metadata can be incomplete. |
| [arXiv](https://arxiv.org) | Free preprints, especially ML and CS | Preprints are not necessarily peer-reviewed. Check for a published version. |
| [ACM Digital Library](https://dl.acm.org) | HCI, systems, and general CS venues (CHI, FAccT, IUI) | Some papers need institutional access; check your university library. |
| [ACL Anthology](https://aclanthology.org) | NLP papers, free and well-indexed | NLP only. |
| Proceedings sites | Official versions: NeurIPS, ICLR, ICML, CVPR, and others | Venue pages differ; check the year and track. |

### Citation chaining

- **Backward:** open the paper's reference list and find the papers it builds on.
- **Forward:** use "Cited by" (Google Scholar) or "Citations" (Semantic Scholar) to find papers that cite it.
- Repeat from the best finds. A paper that appears in several reference lists is worth a look.

### Search tips

- Combine your topic with terms like `survey`, `systematic review`, or `benchmark` (for example, "<topic> survey").
- A survey is a useful starting point, but it can be outdated, incomplete, or biased in what it covers. Check its date and its scope.
- Citation counts can help you find influential work. They are not a measure of correctness or quality.
- Check each candidate's publication status. A preprint is not peer-reviewed by virtue of being on arXiv.

---

## Verification log (this session)

| Entry | Sources opened | Not opened / blocked |
| --- | --- | --- |
| 1 Keshav | Crossref record; first page of MIT-hosted copy | ACM page (403); author's Waterloo page (connection refused) |
| 2 LeCun et al. | Crossref record | Nature page (redirected to login handshake) |
| 3 Adam | arXiv page; ICLR blog | ICLR proceedings page |
| 4 Dropout | JMLR page | Full text |
| 5 ResNet | arXiv page; Crossref record | CVF page (403); IEEE page |
| 6 Attention | NeurIPS page; arXiv page | Full text |
| 7 BERT | ACL Anthology page; arXiv page | Full text |
| 8 GPT-3 | NeurIPS page; arXiv page | Full text |
| 9 Chain-of-thought | NeurIPS page; arXiv page | Full text |
| 10 InstructGPT | NeurIPS page; arXiv page | Full text |
| 11 Sycophancy | ICLR proceedings page; ICLR virtual page; arXiv page | OpenReview (browser check) |
| 12 Kim et al. | FAccT PDF (first page); Crossref record; arXiv page | Rest of paper |
| 13 Kulesza et al. | Crossref record | ACM page; abstract; full text |

No full paper was read in full for this list.
