# 上手指引 / Quickstart

> 写给：第一次接触 CSF、想试着用它做点什么的你。
> For: anyone meeting CSF for the first time and wanting to try it out.

---

## 中文用户

### 这份文档是写给谁的

如果你属于下面任何一种人，这份文档就是为你写的：

- **创业者 / 独立开发者 / 极客**：有想法，但被"还得找人写代码"卡住了。
- **职场中需要工具的人**：财会、产品经理、老师、运营、研究者……日常被重复劳动消耗，想做几个属于自己的小工具。
- **学生 / 研发新手**：在学编程或软件工程，想看看"真正成熟的工程方法"长什么样。
- **任何想认真试一次"和 AI 协作"的人**：你只是好奇这件事的天花板能到哪。

不需要你是程序员，也不需要你已经懂软件工程。

---

### 你真正需要的，只有三样

**1. 你能把目标说清楚。**

不是"写得有多漂亮"，是"你知道自己要什么"。
"我想做一个能帮我自动整理每月发票的小工具"——这就够清楚了。

**2. 你能判断 AI 是不是听懂了，并能纠正它。**

AI 偶尔会理解偏，重点不在"它有没有偏"，而在"你能不能看出来、并且告诉它哪里偏了"。
你不需要给标准答案，你只要能说出"你这里理解错了，我想要的不是 X 而是 Y"。

**3. 你愿意把 AI 当成"一个人"看待。**

不是当搜索引擎，不是当工具。是当成一个**没有记忆但很聪明的合作伙伴**：

- 每次"见面"都要先帮它回忆"我们在干什么"——这就是 `context.md` 的作用。
- 它出错时不要骂它，告诉它"你这里想偏了"——它会立刻学会。
- 它给的方案有问题时，告诉它你的判断和顾虑——它会立刻调整。

**上面三件事，是 CSF 唯一真正要求你具备的能力。其它都是这套方法替你做了。**

---

### 你能做到什么程度

按你想做的事的复杂度，对应不同档位：

| 你想做什么 | 用哪个版本 |
|---|---|
| 体验一下"和 AI 这样合作是什么感觉"（5 分钟） | [`csf-minimal/`](csf-minimal/README.md)（本仓库公开） |
| 做一个简单的小工具、自动化脚本、个人使用的小程序 | csf-minimal 就够 |
| 做一个有正经结构的工具或软件，要持续维护、给别人用 | **csf-lite**（在[知识星球](CONTACT.md)里） |
| 严肃的产品级开发，多角色协作、长周期、复杂业务 | **csf-full**（[联系作者](CONTACT.md)直接协作） |

注意：**版本越深，不是"功能更多"，而是"对协作过程的工程化要求更高"**。一开始用 minimal 完全够。

---

### 第一次该怎么用（5 分钟）

1. 打开 [`csf-minimal/README.md`](csf-minimal/README.md)，读完。
2. 复制 [`csf-minimal/context.md`](csf-minimal/context.md) 到你自己的工作目录。
3. 把 `context.md` 里的"项目信息""当前在做什么"两段填上你的真实情况——一两段话就够。
4. 打开你常用的 AI 工具（ChatGPT / Claude / Copilot / Cursor / 国产模型都行），把 `context.md` 的内容贴进去（或上传文件）。
5. 对它说：**「读这个 context.md，告诉我当前状态和你的建议」**。

走完这五步，你已经在做 CSF 了。

---

### 我希望你养成的几条习惯

这是从 395 次会话的真实使用中提炼出的、对小白最关键的几条。**全部都不需要懂代码**。

#### ① 把别人的 dlog（工作日志）丢给 AI，让 AI 教会你

仓库里 [`_dlog/`](_dlog/) 目录公开了三份**真实的工作日志**——我和 AI 是怎么协作把这个仓库做出来的，**全过程**。

最快的入门方法：

> 「读 csf 仓库的 README、csf-minimal 全部、_dlog 全部。然后告诉我：他们是怎么用 CSF 协作的？我应该怎么学？请用我能听懂的话讲给我听。」

这一句话，会让 AI 把这个仓库读成你的入门导师。**这本身就是 CSF 的实践**——用 AI 解决你看不懂的问题。

#### ② 永远先说"目的"，再说"方法"

❌ 不好：「帮我写一个 Python 脚本，用 pandas 读 Excel，按月份分组求和。」
✅ 好：「我每个月要把发票汇总分类报销。现在每次都要手动整理半天，我想自动化。你看怎么做合适？」

第一种你已经替 AI 决定了用什么语言、用什么库、用什么方式——AI 失去了帮你判断的机会。
第二种你只说了你想要什么——AI 会想清楚之后告诉你它的方案，你判断方案合不合适。

**记住一句话：你说"想要什么"，AI 想"该怎么做"；你判断方案对不对，AI 把方案落地。**

#### ③ 第一句话不是问问题，是建立背景

不要一上来就问"帮我做 X"。AI 不知道 X 在你整体目的中的位置，会给你一个"通用最佳答案"——而通用最佳答案 90% 概率不适合你。

正确的开局：先让 AI 读你的 `context.md`，让它知道**你是谁、在做什么、为什么**，再开始问问题。

#### ④ AI 答错时，不要直接给答案——告诉它"你理解错了什么"

❌ 不好：「不对，应该是 X。」（AI 学不到东西，下次还会犯）
✅ 好：「你这里理解偏了。我说的"客户"不是指注册用户，是指实际付费的人。你重新想一下。」

直接给答案 = AI 这次写对了，下次还会犯。说清楚误解 = AI 这次和未来都会规避。

**这是"把 AI 当人"最具体的体现：你纠正它的理解，而不是替它完成。**

#### ⑤ 重要决策，让 AI 给你"两到三个方案 + 各自代价"

不要让 AI 直接拍板（你失去了判断权），也不要只让 AI 干活（你浪费了它的判断力）。

正确的姿势：

> 「这件事有几种做法？每种做法的代价是什么？你推荐哪种、为什么？」

AI 列方案、说代价、给推荐——你看完后做决定。
**这是 Owner 的位置：定方向；AI 的位置：给选项。**

#### ⑥ 每次对话结束前，让 AI 更新 context.md

最重要的一条，也是最容易偷懒的一条。

> 「我们今天到这里。请你更新 context.md 的"上次对话"和"下次对话"两段，下次开会话我直接读它。」

不更新的代价：下次开会话又从零开始解释。一两次还能撑，第十次你会崩溃。
更新的好处：下次 AI 读完 context.md，第一句话就是"上次我们做完了 X，今天建议从 Y 开始"——零摩擦续上。

---

### 小白最容易犯的两个错

写在最后，因为它们最常见、最致命，也最容易自己识别：

**错 1：把 AI 当搜索引擎，扔个关键词就等答案。**

CSF 不是搜索范式，是协作范式。
你必须说清楚：**你是谁、在做什么、为什么要做、当前卡在哪**。

如果你不愿意说这些，CSF 帮不了你——但说实话，再厉害的工具也帮不了你。

**错 2：不敢打断、不敢纠错，怕"伤害" AI 或显得自己挑剔。**

AI 不在乎，**它需要你的纠正才能稳定输出**。
越早纠错，质量越高；忍着不说，方向偏一次就要回退一大段。

把"挑剔"换成"负责"——这是协作者的本分，不是性格缺陷。

---

### 想做更复杂的事，怎么办

minimal 版做完几个小工具后，你会自然遇到几类新问题：

- "AI 设计的时候和编码的时候经常自己改主意，能不能让它先想清楚再动手？"——这就是 **csf-lite** 引入"角色分离"的原因。
- "有些操作反复做、容易出错，能不能让 AI 每次照着同一个流程走？"——这就是 **csf-lite** 引入"规程库"的原因。
- "AI 同样的错犯了三次，能不能让它从错误里长本事？"——这就是 **csf-lite** 引入"经验库"的原因。

当你**自己**问出这些问题时，再去看 csf-lite。**没问到这一步之前，minimal 就够用了**。
csf-lite 在[知识星球「一个人走」](CONTACT.md)里有完整版。

更进一步是 csf-full——服务于多角色协作、长周期、复杂业务。如果你已经有团队、想把 CSF 引入你们的工程实践——直接[联系作者](CONTACT.md)。

---

### 你不会马上变成专家，但会立刻变得不一样

CSF 不是魔法，不会让你"明天就能做出 App Store 上的产品"。

但用上的第一周，你会发现：

- 你能用清晰的语言把自己的想法说出来——以前你以为"我说不清楚"，其实是"没人逼你说清楚"。
- AI 不再是问什么答什么的搜索框，而是一个**真的帮你想问题**的合作伙伴。
- 你开始有"自己能做点什么"的踏实感——这种感觉以前只有会写代码的人才有。

**这就是 CSF 想给你的：把"和 AI 协作"从一个玄学话题，变成一种你随时可以用的、规范的、可控的工程能力。**

---

## English speakers

### Who this is for

This guide is written for you if you fall into any of these:

- **Founders / indie builders / hackers** with ideas, but stuck at "I'd need
  someone to write the code".
- **Knowledge workers needing tools**: accountants, PMs, teachers, researchers,
  ops folks — anyone tired of repetitive work who wants their own small tools.
- **Students / engineers early in their career** who want to see what a
  *seriously engineered* approach to AI collaboration looks like.
- **Anyone honestly curious** about how far human–AI collaboration can go when
  taken seriously.

You don't need to be a programmer. You don't need to know software engineering.

---

### What you actually need (and that's all)

**1. You can state what you want clearly.**
Not eloquently — clearly. "I want a small tool that auto-organizes my monthly
invoices" is already clear enough.

**2. You can tell whether the AI got it right, and correct it when it didn't.**
You don't have to give the right answer. You just have to be able to say:
"You misread this — I don't mean X, I mean Y."

**3. You're willing to treat the AI as *a person*, not a tool.**
A very smart partner with no memory. Every time you "meet", remind it where you
both are (that's what `context.md` is for). When it goes wrong, tell it where
its understanding drifted — it will adjust. When its proposal seems off, share
your concern — it will rethink.

These three are the *only* real requirements. The rest is what CSF handles for
you.

---

### How far you can go

| What you want to do | Which tier |
|---|---|
| Just feel what "this kind of collaboration" is like (5 minutes) | [`csf-minimal/`](csf-minimal/README.md) — public, in this repo |
| A simple tool, automation, or script for personal use | `csf-minimal` is enough |
| A serious tool or piece of software you'll maintain, others will use | **`csf-lite`** (inside the paid Chinese community) |
| Product-grade development with multi-role, long horizon, complex business | **`csf-full`** — direct collaboration ([contact](CONTACT.md)) |

Higher tiers are not "more features" — they are **stricter engineering of the
collaboration itself**. Start with `csf-minimal`.

---

### How to start (5 minutes)

1. Read [`csf-minimal/README.md`](csf-minimal/README.md).
2. Copy [`csf-minimal/context.md`](csf-minimal/context.md) into your own
   working folder.
3. Fill in the "Project info" and "What we're working on now" sections — a
   sentence or two each.
4. Open whatever AI tool you use (ChatGPT, Claude, Copilot, Cursor, etc.).
   Paste or upload your `context.md`.
5. Say: **"Read this `context.md`, tell me the current state and your
   suggestion."**

Done. You're already doing CSF.

---

### Habits worth forming

Distilled from 395 real sessions. None of these require coding.

**① Hand the project's working logs to the AI and let *it* teach you.**

The repo's [`_dlog/`](_dlog/) folder publishes three **real working logs** — the
full record of how this very repository was built through human–AI
collaboration. The fastest way in:

> "Read this repo's README, all of `csf-minimal/`, and all of `_dlog/`. Then
> explain to me, in plain language, how they used CSF together — and what I
> should learn first."

That single prompt turns this repository into your tutor. *This is itself a
piece of CSF practice* — using the AI to solve "I can't read this yet."

**② Always state purpose first, method second.**

❌ Bad: "Write me a Python script using pandas to read Excel and group by month."
✅ Good: "Every month I have to manually sort and submit invoice expenses. It
takes hours. I'd like to automate it. What do you suggest?"

The first sentence has already locked in language, library, and approach —
removing the AI's chance to think with you. The second sentence shares the
goal, and the AI proposes — you judge.

> *You say what you want; the AI figures out how. You judge fit; the AI
> executes.*

**③ Don't open with a question. Open by establishing context.**

Don't start with "do X for me". The AI doesn't know what role X plays in your
larger goal — it will produce a generic best answer that fits 90% of people
and rarely fits you. Always have it read your `context.md` first.

**④ When the AI is wrong, don't hand it the answer — tell it what it
misunderstood.**

❌ Bad: "No, it should be X." (Worked once, will fail again next time.)
✅ Good: "You misread this. By 'customer' I don't mean registered users — I
mean people who actually pay. Reconsider."

Handing answers fixes one instance. Naming the misunderstanding fixes the
class. *This is what "treating it as a person" looks like in practice — you
correct its understanding, you don't complete its work.*

**⑤ For real decisions, ask for "two or three options + the cost of each".**

Don't let the AI decide alone (you lose direction). Don't reduce it to mere
labor (you waste its judgment). Ask:

> "What are the options here? What does each one cost? Which do you recommend
> and why?"

The AI lists, costs, and recommends. You decide.
*Owner picks direction; AI offers options.*

**⑥ End every session by updating `context.md`.**

The most important habit. The easiest one to skip.

> "We're stopping here today. Please update the 'last session' and 'next
> session' sections of `context.md` so I can pick this up cleanly next time."

Skip it once, fine. Skip it ten times and you'll be re-explaining your project
forever.

---

### The two mistakes beginners make

Both are common, both are fatal, both are easy to spot in yourself:

**Mistake 1: Using the AI as a search engine — tossing keywords and waiting.**

CSF is collaboration, not search. You must say who you are, what you're doing,
why, and where you're stuck. If you won't, CSF can't help you — and frankly,
no tool can.

**Mistake 2: Being too polite to interrupt or correct the AI.**

The AI doesn't mind. **It *needs* your correction to stay reliable.** The
sooner you correct, the better the output. Reframe "being picky" as "being
responsible" — that's not a personality flaw, it's the job of a collaborator.

---

### What about more complex things?

After a few small tools with `csf-minimal`, you'll naturally start asking:

- "Can I make the AI think things through *before* it codes, so it stops
  changing its mind mid-implementation?" → That's why **csf-lite** introduces
  *role separation*.
- "Some operations get repeated and go wrong the same way every time — can I
  make the AI follow one fixed flow?" → That's why **csf-lite** introduces a
  *protocol library*.
- "The AI made the same mistake three times — can it actually learn?" → That's
  why **csf-lite** introduces an *experience library*.

When *you yourself* start asking these questions, look at `csf-lite`. Until
then, stick with `csf-minimal`. `csf-lite` lives inside the Chinese paid
community ([details here](CONTACT.md)).

Beyond that is `csf-full` — for multi-role, long-horizon, complex-business
work. If you already have a team and want to bring CSF into your engineering
practice, [contact me directly](CONTACT.md).

---

### You won't become an expert overnight — but you'll feel different fast

CSF is not magic. It will not put your app on the App Store next week.

But within a week of using it, you'll notice:

- You can articulate your own ideas with a clarity you didn't think you had —
  it turns out you weren't unable to, you just hadn't been forced to.
- The AI stops being a search box and starts being a partner that actually
  *thinks with you*.
- A new feeling settles in: *"I can build things."* That feeling used to be
  reserved for people who could code.

> CSF's offer to you: *turning "collaborating with AI" from a mystical topic
> into an everyday, regulated, controllable engineering capability.*

---

> **本页只讲怎么开始。授权与引用问题请看 [README.md](README.md) 的「授权 / License」与「如何引用」段；联系方式请看 [CONTACT.md](CONTACT.md)。**
> **This page covers how to get started. For licensing and citation see [README.md](README.md); for ways to reach me see [CONTACT.md](CONTACT.md).**
