---
title: Case Study - bang-v3 Development Log Excerpts
layout: default
---

# Case Study: bang-v3 Development Log Excerpts (Sessions 373–375)

[简体中文](README.md) | **English**

> This is the original, raw track record of CSF (Collaboration Specification Framework) running continuously in a real-world commercial project.
> These three sessions demonstrate how CSF functions in practice when uncovering, diagnosing, and repairing a **systemic modular gap**.

---

## Project Context

**bang-v3** is a WeChat Mini-Program + H5 task delegation and forwarding platform. Its core business deals with publishing jobs, tracking forwarding graphs, mapping dissemination trees, and aggregating statistics. At session 373, the project was still actively under development.

The three logs provided in this folder demonstrate more than mere "feature coding"; they present the process of **uncovering, root-cause diagnosing, and repairing a complex architectural oversight** — a systemic omission spanning four independent design layers, discovered after 375 continuous sessions of human-AI collaboration.

*Please note: The original raw dialogue log files in this directory are written in Chinese. English speakers can easily paste them into translation tools (such as DeepL or LLMs) to audit our claims. The precise line links within this document point directly to the raw logs.*

---

## What Happens in These Three Sessions

| File | Session | Highlight |
|---|---|---|
| [dlog-373-发现严重问题.md](dlog-373-发现严重问题.md) | session-373 | Discovered during integration testing that the "Dissemination Overview Column" was never implemented; traced the root cause to find a systemic gap caused by a **temporal race condition and information silos**. |
| [dlog-374-回头梳理转发事件树的问题并定新修改方案.md](dlog-374-回头梳理转发事件树的问题并定新修改方案.md) | session-374 | Discovered that this wasn't an isolated bug, but rather that the entire **node-level stats trigger layer** had never been designed in the first place; initialized a new topic package `tp-374` and established a comprehensive fix (accepting Option A: design-first, code-later). |
| [dlog-375-修改问题.md](dlog-375-修改问题.md) | session-375 | Revised active architectural documents (data schemas + cloud function specs) and **wrote retroactive remarks on outdated historical task briefs** to shield downstream tasks from executing on toxic legacy specs. |

---

## Which CSF Mechanisms Are Displayed

**1. Session Opening**  
Every session strictly starts with "Read context". The AI reconstructs the complete project trajectory from `context.md` in less than 60 seconds — with zero need for the human to tedious-re-explain what we did last time. This remains robust even after 373 continuous iterations.

**2. Purpose-First Navigation**  
Every session is controlled by a clear "Current Task Window" and a "Focus/Red-Dot". When a massive architectural deficit is discovered, the AI explicitly asks whether this is "blocking or non-blocking" before allowing the focal point to drift.

**3. Real-Time Note Taking**  
In `session-373`, the Owner prompts "Take notes on the fly." The AI immediately halts its active analysis, writes down state notes into `session-373.md`, and then resumes. This isn't a conversational gesture — it's a strict operational discipline to shield state continuity.

**4. Explicit Decision Visibility**  
"Option A vs. Option B", "Quick-and-dirty hack for IT-3 first vs. Rigorous redesign before coding" — all options are laid out in plain text with explicit trade-offs. Once the Owner makes a decision, it is permanently locked down.

---

## The Disparity of CSF: Four Concrete Proofs

These four behaviors are not the result of naive "prompt engineering"; they are systemic outcomes born out of CSF's unique structural constraints.

---

### Proof 1: AI openly rejects the Owner's original plan, explains why, and guides the Owner onto a superior engineering path.

The Owner’s initial plan was to push forward with `IT-3` (directly hacking in the UI stats block). After cross-checking historical specs, the AI flags that this path would accumulate massive technical debt. It openly refuses to execute the task as-is and presents a comprehensive argument:

> **"My assessment is that Option A is superior** because node-level cached statistics are a natural responsibility extension of the `statsTrigger`. If we patch in a placeholder UI now and modify the data layer later, we will force ourselves to revisit and recode the Cloud Functions and WXML views — this is exactly what the Owner calls 'fixing a cheap hack latter.' "

— [dlog-374, Line 318](dlog-374-回头梳理转发事件树的问题并定新修改方案.md#L318)

Instead of submissively "just writing the code," the AI holds the line for the project's broader purpose (zero technical debt), pushing back against immediate commands. The Owner reviewed the argument and agreed: "My choice is Option A."

---

### Proof 2: AI takes autonomous decisions and carries out complex tasks based on brief delegated mandates

The Owner mandates: "Execute Plan D. Give me an L3 Brief before you actually start writing files." ([dlog-375, Line 79](dlog-375-修改问题.md#L79)).

The AI then independently reads relevant system specs, maps cross-file dependencies, designs the refactoring flow, and presents a dry-run L3 Brief to the Owner ([dlog-375, Line 131](dlog-375-修改问题.md#L131)). Only after receiving a explicit "Go" from the Owner does it begin modifying files.

This is not "Do exactly what I say step-by-step," nor is it "Ask me everything." It's "Formulate a sound plan independently, align with a brief, and then execute." The human is freed from micro-managing code-level coordinates.

---

### Proof 3: AI self-organizes a complex multi-task roadmap instead of waiting to be spoon-fed tasks

Faced with a single point of failure (the missing overview block), the AI autonomously traces the systemic origin of the failure. **Even before the Owner asks if we need a global structural review** ([dlog-373, Line 349](dlog-373-发现严重问题.md#L349)), the AI is already calculating the blast-radius of the issue.

Immediately after the Owner's inquiry, it outputs a multi-stage roadmap:

> **"We must approach this in two parallel lines**: Line 1 (Process improvement, lightweight, immediate deployment)... Line 2 (Systemic retrospective, moderate layout, requires structured planning)... "

— [dlog-373, Line 427](dlog-373-发现严重问题.md#L427)

Ultimately, the AI created two new topic packages (`tp-373` for cross-scanning and `tp-374` for the node stats layer) inside the filesystem. The Owner only gave a 4-character instruction in Chinese: "Make a plan." ([dlog-373, Line 448](dlog-373-发现严重问题.md#L448)). The breakdown of tasks, setting up tracking files, and updating the global project panorama were all entirely driven and maintained by the AI.

---

### Proof 4: The AI lightning-fast diagnoses a root cause from 30 sessions ago — through semantic specs, without RAG, and without reading full code repos

In `session-373`, while tracing why a specific component package was omitted from the timeline, the AI instantly yields the root cause:

> **"TD-02 was created on 2026-05-19 (Session 138); Major-5 'Mainline Job Presentation' was initialized on 2026-05-21 (Session 168). When TD-02 was frozen, Major-5 did not even exist."**

— [dlog-373, Line 287](dlog-373-发现严重问题.md#L287)

This hyper-precise time-sequence diagnosis (pinpointing exact dates and session indices) was resolved in seconds because the AI matched `TD-02/package.md` against Major-5's metadata — files that CSF mandates must store "creation date + session ID" at initialization. 

No vector searches, no RAG databases, and no indexing of 370 raw logs. Reading just 2 lightweight design specs was enough to catch a race condition across a 30-session history gap.

This highlights a core CSF pillar: **Logs must preserve semantic insights, not low-level chronological chats.** With structured, semantically rich tracking files, the AI can resurrect decisions from deep history instantly. It resembles a human flipping to an indexed notebook, rather than scouring unorganized terminal logs.

---

## How to Read These Raw Logs

These three files are **complete, raw recordings** of actual developer-AI dialogue transcripts, preserving every tool-call trace (searching, reading, editing).

We suggest three ways to explore them:
- **The Fast Scan**: Read only the User segments to understand how the context progresses and drifts over time.
- **The Analytical Read**: Look at the AI's "Conclusion blocks" (usually in bold headers or tables). This is where high-concentration semantic consolidation takes place.
- **The Discipline Watch**: Notice how the AI proactively pauses to draft development notes and asks "blocking or non-blocking" metrics. These events capture the rhythmic engine of CSF.

---

## About CSF

In plain terms, CSF ensures quality in generative software engineering by **externalizing the AI's working memory into the physical filesystem**. This structure ensures every new session reboots on solid ground, and every decision leaves a physical footprint.

No RAG, no multi-agent orchestration code. Just a rigorous collaborative discipline and a continuously-updated `context.md`.

→ [Back to CSF Repository Root](../../README_en.md)
