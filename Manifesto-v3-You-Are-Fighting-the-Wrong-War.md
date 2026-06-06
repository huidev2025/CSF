---
doc_id: 1
title: First Principles (Manifesto)
version: v3.0 (English)
established: 2026-06-06 (translated from Chinese v3 / Phase E full-series rewrite)
status: draft (pending Owner review)
source: 引言v3：你们在拿着前朝的尚方宝剑，斩当朝的官.md
tags:
  - v1_CSF_0529
  - csf
  - manifesto
---

# You're Fighting the Wrong War

> *Every tool you trust was built to tame a machine. AI was never a machine.*

**by dapangangang, with AI**

> In our 373rd session together, the AI was in the middle of a development task. It suddenly stopped and said:
>
> > I've found a design gap here that no plan covers. The root cause has three layers — let me lay them out. We need a redesign; it touches modules at two architectural levels, and we should sweep for similar errors elsewhere. I have two options. You decide. Fixing this will take several sessions. Once you choose, I'll draft the plan.
>
> No one had asked it to look for problems. While doing something else, it found one on its own.

---

## I. You're suffering — and you've blamed the wrong thing

AI-assisted programming has been mainstream for years now. Everyone uses it. Everyone has their tricks. Everyone shares prompt techniques, RAG schemes, context-management strategies, agent orchestration frameworks.

And everyone suffers from the same things:

The AI goes off-course and you don't know why. Long conversations turn to mush. The more complex the project, the less trustworthy the answers get. Some days you spend more time correcting the AI than you would have spent just writing it yourself.

So you decide the model isn't strong enough — and you wait for a better one. A better one arrives. The problem stays.

You decide your prompts aren't precise enough — and you study prompt engineering. The tricks multiply. The problem stays.

You decide the context window isn't long enough — and you bring in RAG, vector databases, more and more information shoveled into the model. The information multiplies. The problem stays.

None of these directions are wrong, exactly. You're just applying the previous dynasty's Law to the problems of a new era.

You're wielding the wrong dynasty's sword on the wrong dynasty's official. Every one of these tools — RAG, agent frameworks, ever-more-precise prompts — was forged on the same assumption:

**AI is a powerful machine, and our job is to eliminate its errors and patch its defects.**

That assumption is wrong at the root.

---

## II. Making mistakes is the nature of intelligence — not a defect of it

AI is *artificial intelligence*. Not artificial execution. Not artificial retrieval. Not artificial autocomplete. **Intelligence.**

Any system that genuinely works with concepts and infers intent will, by its nature, sometimes be wrong. This isn't a defect — it's a constitutive property of intelligence. **A system that never errs isn't a better intelligence. It isn't an intelligence at all.** It's just a machine doing deterministic mapping.

What you've been doing, all this time, is trying to strip the AI of its uncertainty. Every layer of "improvement" pushes the intelligent system one step closer to a machine. Then you complain it isn't useful.

Of course it isn't useful. You are actively eliminating the very thing that makes it useful.

The right question was never *how do I stop the AI from making mistakes.* The right question is *how do I work effectively with an intelligence that can be wrong.* These are two entirely different questions, and they lead in two entirely different directions.

---

## III. I saw a wide-open space here

I haven't invented anything new. I just took two facts that everyone knows but no one really accepts — and followed their logic as far as it would go.

What I saw was a space no one had seriously cultivated:

**Within the nature of the LLM, using natural language and purpose, design a complete engineering system for human–AI collaboration.**

Not a pile of tricks. Not a few templates. (Though I did get tricks and templates along the way — and they really do work.)

- **Purpose** is the semantic control unit of any meaning-bearing system.
- Knowledge has layers; information flows in one direction.
- **The human discerns and chooses the direction; the AI carries out the work.** (Not "calibrates" in the mechanical sense — it's a local judgment, made deliberately.)
- Quality assurance doesn't come from format constraints. It comes from translating the implementation back into business language, so human intuition can catch the drift.
- The system learns from every execution. Capability grows over time — independently of the underlying model.

I spent nearly four hundred sessions exploring this space. I built a piece of software along the way, and almost as a side effect, I established the **CSF** — a framework that runs from first principles all the way down to engineering practice.

What you'll find here is the smallest possible door into it. Walk in, and you'll see: one context file, one rhythm of work, and within a few conversations, a difference you can feel. This is the entrance. It is not the whole.

Behind the door is the full framework. I'd like to invite you to explore this unfamiliar space with me.

---

## IV. The Pang Principle

"Pang" is a Mandarin sound — fourth tone — the verbal shrug of *"oh, of course we all already knew that."*

(It's not really a "principle." Call it a reminder. The name is a small joke — a nod to Huawei's *Tao Principle.*)

> **Axiom.** A natural-language expression carries far more information than a symbolic one.

> **Fact ①.** The value of artificial intelligence comes from its *intelligence.* Trying to make it as reliable as a machine is exactly the act of destroying that value.

> **Fact ②.** Over time, the information a single expression has to carry grows — inevitably, everywhere, without exception — and its semantics get diluted.

---

*— dapangangang, 2026*

*A minimal, hands-on version of CSF (Collaboration Specification Framework) lives in this same repository.*
*Five minutes to start; a few sessions to feel the difference.*
*Want to go deeper — get in touch.*
