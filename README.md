# zak-skills

A collection of opinionated workflow skills for Claude Code, focused on shipping non-trivial features faster while spending fewer Opus tokens.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-1-green.svg)](#skills-in-this-collection)
[![Built for Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-orange.svg)](https://docs.claude.com/en/docs/claude-code)

> **Pre-1.0.** The four-layer pattern is stable and used in real work, but interfaces and edge cases will keep moving until 1.0. Pin a tag if you depend on it.

---

## What this is

A focused set of Claude Code skills that codify a single thesis: **stop using your most expensive model to do mechanical work**.

The first skill in the collection — `zak-delegator` — is a four-layer orchestration pattern that splits a non-trivial task across the right model at each step:

- **Opus** plans once and reviews once.
- **Sonnet** does the orchestration in between (the biggest cost lever in the pattern).
- **Codex** does the mechanical implementation work via the `codex-delegate` companion skill.
- **Sonnet / Opus subagents** handle the actual coding, routed by complexity.

In practice, the largest saving comes from moving orchestration off Opus — orchestration touches every step, so this single switch compounds across a feature. Exact savings depend on task shape; measure your own runs before quoting a number. Speed improves through pipeline-with-parallelism, and quality is protected by a hard human checkpoint before commit.

---

## Why bother

Two patterns dominate Claude Code today, and both leave value on the table:

| Pattern | Problem |
|---|---|
| **Opus-for-everything** | Burns the most expensive token rate on mechanical typing. Slow, because a single context handles every step sequentially. |
| **Sonnet-for-everything** | Cheap, but skips architectural review. Accumulates subtle design debt and silent bugs. |

`zak-delegator` is the routing layer that lets you avoid both. It is not a new agent runtime, not a tool, not a framework. It is a skill — a contract Claude reads at the start of a task that tells it *how to think about the work before doing it*.

---

## Installation

### Via the `skills` CLI (recommended)

```bash
npx skills add Youssef-Eltohamy/zak-skills --agent claude-code
```

This installs every skill in the collection into `~/.claude/skills/`.

### Manually

```bash
git clone https://github.com/Youssef-Eltohamy/zak-skills.git
cp -r zak-skills/skills/zak-delegator ~/.claude/skills/
```

### Companion skill

`zak-delegator` references `codex-delegate` for the mechanical-implementer role. If you want the full pattern, install both:

```bash
npx skills add amElnagdy/delegate-skills --agent claude-code
```

`codex-delegate` requires the OpenAI Codex CLI to be installed and authenticated. See its [README](https://github.com/amElnagdy/delegate-skills) for details. `zak-delegator` works standalone as well — it will route everything through Claude subagents if Codex is unavailable.

---

## Quickstart

Skills in Claude Code are triggered by their `description` matching your prompt, not by slash commands. So you invoke `zak-delegator` by *describing the kind of work it covers*, naming it explicitly if you want to be sure:

```
I have a feature ready to implement (specs are done). Use the
zak-delegator skill to produce a Layer-1 implementation plan,
then we'll execute it stage by stage.
```

Claude will load the skill, write a plan with the routing metadata baked in (classification per step, explicit dependency graph, pipeline stages), and wait for your signal to start executing. From there, run each stage using the ready-to-paste prompts in [`USAGE.md`](skills/zak-delegator/USAGE.md).

If you want to be extra explicit, the underlying Skill tool can be called directly:

```
Use the Skill tool to load zak-delegator, then plan my feature.
```

Either way works — the description-matching path is the standard one.

---

## How it works

The pattern has four layers. Each layer uses the model best suited to its kind of work.

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1 — Planning              (Opus, once)           │
│     decompose + dependency graph + classify + pipeline  │
├─────────────────────────────────────────────────────────┤
│  Layer 2 — Orchestration         (Sonnet)               │
│     dispatch + collect + sequence + escalate            │
├─────────────────────────────────────────────────────────┤
│  Layer 3 — Execution             (mixed)                │
│     Codex (mechanical) / Sonnet (standard) / Opus (hard)│
│     parallel within stages, sequenced across stages     │
├─────────────────────────────────────────────────────────┤
│  Layer 4 — Review                (Opus, once)           │
│     diff + gates + scope check → human commits          │
└─────────────────────────────────────────────────────────┘
```

The full architecture lives in [`SKILL.md`](skills/zak-delegator/SKILL.md). The short version: planning and review are where the expensive thinking belongs; everything else is mechanical and should be priced accordingly.

---

## The 3-question classifier

Every subtask in the plan gets classified by answering three questions, in order:

1. **Can I write the spec in three sentences?** → If yes, Codex (for mechanical work) or Sonnet (for standard reasoning). If no, go to question 2.
2. **Is the pattern obvious from existing code in the repo?** → If yes, Sonnet. If no, go to question 3.
3. **Does it require architectural judgement or hard debugging?** → If yes, Opus. If no, you misclassified at step 2; recheck.

The classifier is deliberately crude. Three questions, one branch each. Resist the urge to invent more axes — they erode the rule's value.

---

## When to use this

Reach for `zak-delegator` when:

- You are about to start a feature, refactor, or migration that touches multiple files.
- You have a specs document and are about to write the implementation plan.
- You want to run a queue of bounded mechanical tasks (scaffolds, removal sweeps) without burning Opus tokens.
- You are tired of Opus typing boilerplate at $15/MTok.

Skip it when:

- The task is one file and one function. Just do it inline.
- You are still in exploration / research mode. Brainstorm first, then plan, then orchestrate.
- You want Claude to write code directly without delegating. That is a different mode.

---

## Examples

Two illustrative walkthroughs — realistic task shapes that show how the pattern's pieces fit together. Treat them as worked thought-experiments, not transcripts; real runs will vary in the details.

- **[Adding a Telegram channel to a NestJS API](skills/zak-delegator/examples/rplya-telegram.md)** — five steps, three models, one parallel stage.
- **[Migrating a Flutter app from `StatefulWidget` to hooks](skills/zak-delegator/examples/flutter-migration.md)** — high-volume mechanical migration with hidden judgement calls.

Each walkthrough covers Layer 1 → Layer 4: the plan, the dependency graph, the routing decisions, and where each layer earns its keep.

---

## Skills in this collection

| Skill | Purpose |
|---|---|
| [`zak-delegator`](skills/zak-delegator) | The four-layer orchestration pattern: Plan(Opus) → Orchestrate(Sonnet) → Execute(mixed) → Review(Opus). |

More skills will land in this collection over time. The bar for inclusion: a skill must encode a workflow opinion that survives across projects, not just a snippet that happens to be reusable.

---

## FAQ

**How is this different from `codex-delegate`?**
`codex-delegate` is the mechanical-implementer step — it lets you hand a single bounded task to Codex and review the diff. `zak-delegator` is the layer above: it tells Claude *when* to call `codex-delegate`, when to route to Sonnet instead, and when to keep the work on Opus. They compose.

**How much does it actually save?**
Depends on the task. The dominant lever is moving orchestration off Opus — orchestration touches every step, so the saving compounds. On a multi-step feature in my own work the difference is large enough to feel; on a one-step task it's not worth the overhead. Run your own measurements before quoting a number to anyone.

**What if the routing is wrong?**
Every subagent is told to stop and report when confidence drops below ~90%. The orchestrator escalates to Opus on a stop, and to the human on a second stop. This catches the "looked easy, turned out hard" failure mode that pure upfront classification misses.

**Why is commit-time still manual?**
Because commits are the one boundary you cannot un-cross cheaply. Layer 4 gives you a clean diff and gate results; your judgement is the last check before it ships.

**Can I use this without the `superpowers:writing-plans` skill?**
Yes. `writing-plans` defines the plan's *structure*; `zak-delegator` defines its *routing metadata*. They compose. If `writing-plans` is unavailable, the planner is still on the hook for the same three Layer-1 enrichments (atomic subtasks, dependency graph, classification).

---

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the bar a skill needs to clear before being added to this collection.

---

## License

[MIT](LICENSE). Use it, fork it, ship with it.

---

## Author

**Youssef Eltohamy** ([@Youssef-Eltohamy](https://github.com/Youssef-Eltohamy))
