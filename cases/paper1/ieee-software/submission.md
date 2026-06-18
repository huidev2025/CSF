# When Adding More Rules Made AI Worse: Index Sickness and How We Cured It

**Hui Zhang (张慧)**
Shenzhen Yunxi Technology Co., Ltd.
zhanghui@ecloudriver.com

**Shuren Song (宋树仁)**
Information Technology Center, Tsinghua University
songsr@tsinghua.edu.cn

---

## Abstract

We built a symbolic identifier system, accumulated defensive rules in our AI's system prompt, and refined our constraints over 220 sessions. By Session 222, the AI was confidently reciting completed work that had no connection to physical files. We had built what we now call **Index Sickness**: AI stops reasoning about the actual problem and starts reasoning about its own symbol system.

The fix was not better constraints. It was removing almost everything.

This article documents 391 sessions of long-horizon AI-assisted software development, two rounds of simplification with opposite results, and the architectural pattern that substantially reduced failures and eliminated Index Sickness: separate current state from process history, physically, so historical noise cannot enter context in the first place. The mechanism requires no middleware, no model upgrade, and no graph architecture—just two files with different write modes.

**Keywords**: human-AI collaboration, LLM context management, semantic space control, software engineering, action research

---

## I. The Problem We Created

### How We Broke Our AI Collaboration—Twice

We were building Bang-v3: a WeChat mini-program and H5 forwarding platform, refactoring ~506 files across roughly one month. One Owner (the human practitioner directing all AI collaboration), two AI roles (a Chief-of-Staff and a Developer), 391 sessions. The Owner handled all business and engineering discussion; no code or specification was written by hand. Each session began with the AI reading `context.md` to reconstruct its own working context—where the project came from, where it now stands, and where it is going; at session end, the AI updated `context.md` accordingly. No re-briefing was required.

By the midpoint, things had gone badly wrong in a way we did not expect. AI was not forgetting—it was *too faithful* to its own symbolic record. Every time something broke, we added a rule. Every time a task got complicated, we gave it a symbol code. The AI's system Instructions grew to **308 lines** of defensive patches. And the AI got worse.

At Session 215, the AI Chief-of-Staff fully recited a completed "Pending-Flow v2 Legislation Proposal." The logic was internally consistent at the symbolic level. When the Owner ran `grep` on the physical files, none of it existed. AI had built a complete "completed state" in its symbol layer while being entirely disconnected from reality. We called this **Index Sickness**: AI stops reasoning about the actual problem and reasons about its own symbol system instead.

This is not a rare edge case. It is, we argue, the predictable endpoint of the prevailing engineering response to LLM unreliability: add more structure, add more symbols, add more rules. Our record shows this trajectory eventually produces its opposite.

**Project records are open-sourced at https://github.com/huidev2025/CSF.**

### 1.1 A Note on This Paper

All prose in this paper was produced by the AI collaborator (GitHub Copilot, primary model: Claude Sonnet 4.6, supplemented by Claude Opus 4.7) under the Owner's direction; the Owner did not independently write any paragraph. This is disclosed as a methodological transparency requirement. All empirical data—session sequence numbers, file change records, and the systematic analysis of 1,242 Owner inputs—are grounded in verifiable session records, not AI-generated claims. Full records are open-sourced. In this sense, the paper itself is an instance of the mechanism it describes: a long-horizon collaborative artifact produced under Purpose-First context management—direct evidence that purpose-activated AI maintains the semantic vitality required for sustained complex work.

---

## II. What Went Wrong—and Why

### 2.1 The Failure

The failures took two forms. The first was spatial: inside a single session, the symbol system created cognitive loops. Each identifier required a look-up-and-map step; once an identifier's mapping was incorrectly resolved, all subsequent reasoning "corrected" itself within the symbolic system, forming a closed loop detached from business reality. The Owner could no longer check AI's output by intuition—errors surfaced only at physical execution, often after significant downstream work.

The second was temporal: across sessions, deprecated decisions did not fade. When the Owner explicitly declared a scheme deprecated, the Transformer self-attention mechanism had no way to honor that declaration. Historical symbolic patterns maintained weight in subsequent sessions and quietly infiltrated new design documents. Engineering log D-108 records the canonical case: AI used residual impressions to complete field label TD-01 as "024 Reverse Challenge Plugin." TD-01 was the H5 Shared Component Library. The error spread to 13 cross-file labels; the entire session was reclassified as a "meta-incident repair session."

These failures have quantitative backing from independent sources. Chroma's systematic tests across 18 LLMs found that distractors in context cause non-monotonic performance degradation even under ideal retrieval recall [1]. Raju et al. found that agent task success rates drop sharply after forced context extension even when all relevant content is present [2]. The problem is not retrieval—it is what is already in the window.

We label the underlying dynamic **Index Sickness**: when symbolic systems reach sufficient density, AI's attentional resources concentrate in the symbolic layer and real business semantics are structurally marginalized. The canonical manifestation—AI generating outputs that are internally consistent but physically disconnected—we call **Phantom Legislation**. This is distinct from ordinary hallucination: hallucination produces content that is internally inconsistent or factually ungrounded; Index Sickness produces outputs that are internally consistent within the symbolic layer but disconnected from physical reality—the AI is reasoning correctly about the wrong thing.

### 2.2 Why Intuition Fails Here

The dominant engineering response to LLM unreliability—add more formal constraints, refine symbols further, accumulate rules—is not irrational in the short term. For single-session, narrowly scoped tasks, it often works. The failure mode only emerges at scale and over time, which means the feedback loop reinforces the wrong lesson: "this rule fixed the problem in Session 50" does not warn about what that rule is doing to Sessions 150, 215, and 300.

Recent work on structured memory architectures [3][4][5] and prompt formalization [6][7] addresses the same challenge this project faced—context degradation in long-horizon LLM collaboration. These are real tools for a real problem. However, what our record adds is a counterexample: in our project, moving in that direction produced Index Sickness. Whether that result generalizes is an open question; the counterexample is offered for examination, not as a refutation.

---

## III. What We Learned

### 3.1 Three Observations That Guided the Redesign

After Index Sickness, we stopped adding rules and started asking why natural language had been working better in the sessions where things went well. Three things became clear:

**1. Symbols cost attention.** Natural language activates the model directly through trained priors. Symbols require look-ups. When a note says "this module handles the forwarding chain," AI accesses meaning immediately. When a note says "SEC-2.0 governs D-139," AI must first resolve the identifiers—consuming attention that should go to the actual problem. At some threshold, look-up load crowds out comprehension.

**2. Determinism eliminates the reason for using AI.** LLMs are useful because they can reason flexibly across ambiguous inputs. Formal constraints require AI to allocate attention between format compliance and semantic accuracy. More precise constraints produce more format-correct, less semantically accurate outputs. At the extreme, this is Phantom Legislation.

**3. "Deprecated" does not mean gone.** The Transformer attention mechanism allocates weights by statistical co-occurrence. A symbol that appeared 50 times does not lose weight because it was declared obsolete in a human note. Expanding the context window does not solve this—it may worsen it by accommodating more historical discussion.

These are not new theoretical claims. They follow from what LLMs actually are. What was missing was a practical mechanism that operated on these observations instead of against them.

**Naming note**: we call this cluster of observations the **Pang Principle**—from the Chinese colloquial image of a self-evident truth thudding into place.[^1] The name signals intent: this is not a discovery, it is a reminder of something that was always true and was being systematically ignored in our project and in the engineering path we were following.

---

## IV. The Fix: Baseline-Log Physical Separation

### 4.1 The Core Idea

Do not try to fight historical noise inside the context window—prevent it from entering in the first place.

This mechanism requires no middleware code, no model upgrade, and no graph architecture. It restructures how project documentation is physically organized into two files with two different write modes:

**Baseline (`context.md`) — Overwrite mode.** Stores only the current task triple: Purpose, Method, and Resources. After each task, the baseline is rewritten with the new state. No history is retained. The session always starts from a clean statement of "what we are doing now and why."

**Session Log (`session-NNN.md`) — Append mode.** Records each session's process: how decisions formed, what alternatives were considered and eliminated, why, and what corrections were made. Natural-language writing only—not excluding filenames and symbolic references, but requiring natural-language explanation alongside every entry. Subsequent readers can then reconstruct context through reading comprehension rather than mechanical retrieval.

The baseline crosses into new sessions; session logs do not. Deprecated content cannot affect new tasks because it is physically absent.

### 4.2 Why "Purpose First"

Baseline-Log Separation is the architectural implementation of a more fundamental insight: purpose is the minimal input that maximally preserves AI's semantic vitality.

The baseline stores Purpose before Method before Resources—not as a stylistic choice, but because purpose is the lightest possible input that constrains AI's interpretive space. Format constraints operate at the token layer. Symbolic identifiers require look-ups. Purpose operates at the semantic layer, directly aligning AI's probabilistic activation toward the current task boundary.

When AI first reads "why we are doing this," it draws on its own knowledge to select appropriate methods and identify just-sufficient resources—without a retrieval intermediary, because knowing the purpose, AI naturally knows what to look for.

### 4.3 Results

After implementing Baseline-Log Separation around Session 215–252:

| Dimension | Before | After |
|---|---|---|
| AI Instructions | 308 lines (defensive patches) | ~80 lines (↓75%) |
| `context.md` | 680 lines | 189 lines (↓72%) |
| DEVNOTES decision entries | 141+ entries | 5 entries (↓96%) |
| Owner correction density | 0.79/session (#136–#214) | 0.53/session (#253–#395, ↓33%) |
| Index Sickness cases | 9 confirmed | 0 cases across ~150 sessions |

The correction density figures come from systematic analysis of 139 session record files covering Sessions #136–#395: 1,242 Owner inputs extracted, classified by keyword matching plus manual review, with Index Sickness cases individually verified against the operational definition. Classification keywords, manual review criteria, and raw data are documented and open-sourced (see `cases/paper1/dlog/data-analysis/owner_verbatim_stats_v3.md` in the repository). Formal statistical testing is not reported here: this is a practitioner-oriented action research report, and the underlying data are open-sourced precisely so that researchers who require statistical inference can apply their own methods.

> **Note**: Per-session token consumption was not systematically recorded. No Index Sickness cases were observed: across the subsequent ~150 sessions, the Owner never encountered "AI claimed completion but physical file verification found it disconnected," and no meta-incident repair sessions occurred. Interaction patterns simplified to "start, confirm, end."

### 4.4 The Critical Comparison: Two Rounds of Simplification

The results above would be consistent with a simpler explanation: we just got better at the project over time. We have a specific counter-argument.

Before Baseline-Log Separation, we tried a different simplification round ("SP-Trim," Sessions ~136–141): quantitative reduction, cutting specification lines by ~56%. The results:

| | SP-Trim (~Sessions 136–141) | Baseline-Log Separation (~Sessions 215–252) |
|---|---|---|
| Core strategy | Delete rules, merge files | Separate baseline from log |
| Specification change | ~1,100 → 480 lines (↓56%) | Instructions 308 → 80 lines (↓75%) |
| `context.md` | 2,197 → **2,256 lines (+2.7%, grew)** | 680 → **189 lines (↓72%)** |
| Index Sickness post-change | **Still erupted** (Session 215 Phantom Legislation) | **0 cases** across ~150 sessions |

At SP-Trim, we had already accumulated ~140 sessions of experience. If improvement came from learning, it should have appeared then. The counter-evidence is not that SP-Trim's six-session window was clean—it is that Index Sickness erupted in concentrated form in the ~60–80 sessions that followed SP-Trim, despite that accumulated experience, and only stopped when the architecture changed.

The effective variable was not how many lines of specification we had—it was whether current-state information and historical-process information were physically separated. SP-Trim reduced volume but kept both types mixed in the same files. Baseline-Log Separation split them.

---

## V. What This Means for Your Project

### 5.1 Try This

The mechanism is simple enough to implement this week:

1. **Create two files**: `context.md` (overwrite mode) and `session-log.md` (append mode). Keep them physically separate.
2. **Baseline format**: Write Purpose first, then Method, then Resources. Rewrite the entire baseline after each significant task—do not annotate or patch the previous version.
3. **Log format**: Record decisions in natural language. When you eliminate an option, write one sentence explaining why. Future-you and future-AI both need to know.
4. **Context loading rule**: Start new AI sessions by loading only the baseline. Load session logs only when explicitly tracing a past decision.

This is the entire mechanism. No middleware, no vector store, no framework.

### 5.2 What to Watch For

Index Sickness symptoms: AI reciting completed work that does not match physical files; corrections that require you to "explain the project again from the top"; session titles shifting toward "failure investigation" and "start over." If you are seeing these, check whether your active context is accumulating historical discussion. The diagnosis is often simpler than the symptom looks.

### 5.3 Scope and Threats to Validity

This record comes from a single project, one Owner, one AI platform (GitHub Copilot, Claude Sonnet 4.6). Action research methodology—where the researcher is simultaneously the practitioner—is recognized in software engineering [8][9]; in contexts of deep LLM involvement, this framework may better capture cognitive phenomena in real interaction than controlled experiments [10].

**Internal validity**: The most plausible alternative explanation is a learning effect—the Owner became more skilled over time. The SP-Trim comparison (§4.4) directly addresses this: SP-Trim was attempted after ~140 sessions of accumulated experience and Index Sickness still erupted in concentrated form in the sessions that followed. Improvement came only when the architecture changed, not when experience accumulated. We cannot rule out concurrent changes in task complexity or model version; we have no record of such changes in that period.

**External validity**: Generalizability requires validation across more projects, collaborators, and LLM versions. We are not claiming the mechanism solves every long-horizon AI collaboration problem, or that the supply-side approaches it contrasts with are wrong in general. We are offering a counterexample and a mechanism, available for examination and attempted reproduction.

Multi-project comparison is the most direct next step. We invite it.

---

## Acknowledgments

This paper was produced under the Baseline-Log Physical Separation protocol described above. H. Zhang was responsible for purpose activation—stating direction, rendering judgment, and raising corrections; all prose was generated by the AI collaborator. AI involvement is declared in full, consistent with §1.1.

---

[^1]: *乓的一声* (pāng de yī shēng): a Chinese colloquial onomatopoeia for something clicking unmistakably into place.

## References

[1] Hong, K., Troynikov, A., & Huber, J. (2025). "Context Rot: How Increasing Input Tokens Impacts LLM Performance." Chroma Technical Report. https://trychroma.com/research/context-rot

[2] Raju, R. et al. (2026). "The Limits of Long-Context Reasoning in Automated Bug Fixing." *ICLR 2026 ICBINB Workshop*. arXiv:2602.16069.

[3] Zhang, Y. et al. (2026). "CoMem: Context Management with A Decoupled Long-Context Model." arXiv:2605.30842.

[4] Lu, K. et al. (2026). "REAL: A Reasoning-Enhanced Graph Framework for Long-Term Memory Management of LLMs." arXiv:2606.10694.

[5] Wu, Z. et al. (2026). "GAM: Hierarchical Graph-based Agentic Memory for LLM Agents." arXiv:2604.12285.

[6] Chen, Z. et al. (2026). "Promptware Engineering: Software Engineering for Prompt-Enabled Systems." *ACM TOSEM*. arXiv:2503.02400.

[7] Wu, J. et al. (2025). "Git Context Controller: Manage the Context of LLM-based Agents like Git." arXiv:2508.00031.

[8] Staron, M. (2024). "Teaching Action Research." *EMSE Edu Book*. arXiv:2408.02399.

[9] Wohlin, C. et al. (2012). *Experimentation in Software Engineering*. Springer.

[10] Treude, C. & Storey, M. (2025). "Generative AI and Empirical Software Engineering: A Paradigm Shift." *AIware 2025*. arXiv:2502.08108.

