---
name: zak-delegator
description: Use this skill whenever the user is about to start a non-trivial multi-step coding task, building a feature, refactoring across files, scaffolding a module, executing an implementation plan, or any work that touches multiple subtasks. Triggers on phrasings like "let's plan and build", "split this into subtasks", "orchestrate this", "delegate this", "let's execute the plan", "let's tackle this feature", or whenever the user starts work right after a specs/planning phase. Also use proactively when you see a task that would benefit from being decomposed and routed across models (Opus / Sonnet / Codex) for cost-and-speed optimization, EVEN IF the user does not explicitly ask for orchestration. Encodes a four-layer pattern (Plan → Orchestrate → Execute → Review) that ships faster while spending ~60% less on Opus tokens, with a quality safety net. Do NOT use for trivial single-file edits, one-off questions, or pure research tasks.
metadata:
  version: 0.1.0
  author: Youssef El-Tohamy
---

# Zak Delegator

A pattern for shipping non-trivial coding tasks fast, cheaply, and with quality protection, by routing each step to the right model instead of using one model for everything.

You are the **orchestrator**. You decompose, route, collect, and decide. You do NOT do all the thinking yourself with the most expensive model. The whole point: route by cognitive load.

## Why this pattern exists

Two failure modes this skill prevents:

- **Opus-everywhere**: slow (single context, sequential), expensive (Opus rate on every token, including mechanical typing).
- **Sonnet-everywhere**: cheap but skips architectural review, accumulates subtle bugs and design debt.

This skill encodes a four-layer pattern that gives you:

- **Real cost reduction**: by moving orchestration off Opus, the single biggest saver, and pushing mechanical work to Codex or Sonnet, you shave a meaningful chunk off the Opus bill on multi-step tasks. The exact saving depends on the task shape; measure your own runs before quoting a number.
- **Real speedup**: pipeline-with-parallel-inside-stages, not sequential.
- **Quality safety net**: Opus reviews the diff before commit, so cheap-model failures cannot ship.

---

## The four layers

### Layer 1: Planning (Opus, once)

The planning pass MUST use Opus. Quality here determines every downstream decision; cheaping out is false economy.

**Compose with `superpowers:writing-plans`.** That skill defines the plan's *structure* (steps, acceptance criteria, testing notes, scope). This skill defines the *routing metadata* the plan must carry on top of that structure. Use both: invoke `writing-plans` to produce the plan in its canonical form, then ensure every step in that plan carries the three Layer-1 enrichments below. If `writing-plans` is unavailable, the planner still owes the same enrichments, they are not optional.

The planner produces, for the given task:

1. A list of atomic subtasks (one task = one brief = one commit). These map directly to `writing-plans` steps.
2. A dependency graph: which subtask blocks which. Make this explicit, not implicit in step ordering.
3. A classification per subtask using the 3-question classifier below, annotate each step with `→ Codex` / `→ Sonnet` / `→ Opus`.
4. A pipeline of stages, with parallel-where-possible inside each stage. Group steps by which stage they belong to.

The output of Layer 1 is a `writing-plans`-shaped plan, enriched so the next layers can execute it mechanically.

### Layer 2: Orchestration (Sonnet, not Opus)

This is the biggest cost lever in the whole pattern. Orchestration itself is mechanical work:

- Read the plan from Layer 1.
- Dispatch subagents per the classification.
- Collect results, check completion.
- Advance to the next pipeline stage.
- Handle escalations.

Sonnet is sufficient and noticeably cheaper than Opus for this. Use Opus as orchestrator ONLY when the orchestration itself involves a nontrivial decision (rare, usually it does not).

**How the handoff actually happens.** The Opus thread that produced the Layer-1 plan does not orchestrate. It spawns a Sonnet subagent via the `Agent` tool with `model: sonnet` (or the platform's equivalent) and hands it the plan as its initial prompt. From that point on, the orchestration tokens are Sonnet tokens, not Opus tokens. The Opus thread idles until Layer 4. If you skip this handoff and let Opus orchestrate "informally" from the same thread, you keep paying Opus rates for every dispatch and the cost-saving claim of this pattern silently disappears.

### Layer 3: Execution (mixed, by classification)

Each subtask is dispatched to one of three implementers:

| Implementer | Use for | How |
|---|---|---|
| **Codex** | Mechanical work: scaffolding, migrations, removal sweeps, tests-from-spec | Use the `codex-delegate` skill |
| **Sonnet subagent** | Standard coding with a pattern visible in the codebase | `Agent(subagent_type: claude, model: sonnet)` or equivalent |
| **Opus subagent** | Architectural decisions, complex debugging, ambiguous specs | `Agent(subagent_type: claude, model: opus)` or equivalent |

Inside each pipeline stage, run independent subtasks in **parallel**. Across stages, sequence them. True parallel requires no shared state between subtasks; if a subtask needs output from another, it belongs in a later stage.

### Layer 4: Review (Opus, once before commit)

Before any commit, the orchestrator escalates back to Opus for review:

1. Read the full diff.
2. Re-run the project's gates yourself, do NOT trust subagent self-reports.
3. Check scope: did each subagent do exactly what its brief said, nothing more, nothing less?
4. Either approve commit, or send specific subtasks back for rework.

The commit boundary is yours alone. Subagents never commit. Codex specifically cannot commit reliably, this is documented in the `codex-delegate` skill.

---

## The 3-question classifier

For each subtask, ask in order. Stop at the first "yes":

1. **Can I write the spec for this subtask in 3 sentences or fewer?** → Yes: candidate for Codex (if mechanical) or Sonnet (if needs light reasoning). No: go to 2.
2. **Is the implementation pattern obvious from existing code in the repo?** → Yes: Sonnet subagent. No: go to 3.
3. **Does this require an architectural decision, a tricky debugging session, or resolving ambiguous requirements?** → Yes: Opus subagent. No: re-examine question 2, you probably misclassified.

The classifier is intentionally crude. Three questions, in order. Do not invent additional axes.

---

## The escalation pattern (safety net)

Every Sonnet or Codex subagent gets an explicit instruction in its brief:

> "If you are less than ~90% confident in your approach, stop and report what you are unsure about. Do not guess. We would rather burn an escalation than ship a wrong implementation."

When a subagent stops:

1. The Sonnet orchestrator escalates to an Opus subagent, passing the original brief + the subagent's uncertainty report.
2. If Opus also reports uncertainty, the orchestrator escalates to the user.

This prevents the classic failure where Sonnet "almost gets it" for 20 minutes, ships something subtly wrong, and you only find out at review time after spending the tokens.

---

## When to use Codex specifically

Codex (via the `codex-delegate` skill) is a separate runtime, different model, different billing. Its tokens do not count against Claude usage. Note this is not "free", it is billed by OpenAI on your Codex/ChatGPT plan or pay-as-you-go, just on a different invoice. The win is shifting mechanical work off your Claude bill, not eliminating cost.

**Use Codex for:**

- Mechanical migrations (e.g. converting all `StatefulWidget` to `HookWidget`, replacing one API with another across files).
- Repetitive scaffolding (e.g. five modules with the same NestJS controller/service/DTO structure).
- Removal sweeps (e.g. deleting all references to a deprecated feature).
- Generating tests from a clear spec.

**Do NOT use Codex for:**

- Tasks small enough to do inline, the brief-writing overhead is not worth it.
- Ambiguous bug fixes that need full codebase context, Codex sees only the brief.
- Design decisions, Codex implements, it does not architect.

Codex requires writing a self-contained brief (it has no chat memory, no repo memory). Spending Opus tokens to write a precise brief is fine, it is cheaper than spending Opus tokens to implement the work itself.

---

## Concrete worked example

Task: "Add a Telegram channel integration to a multi-channel NestJS backend, parallel to the existing WhatsApp integration." (This walkthrough is illustrative, it shows the pattern's shape on a realistic task, not a literal transcript of a single run.)

**Layer 1, Opus planning produces:**

```
Subtasks:
  A. Create TelegramModule scaffold (controller + service + DTOs)
     - Spec: 2 sentences. Pattern: copy from WhatsAppModule.
     - Classification: Codex (mechanical scaffold).

  B. Implement Telegram webhook receiver in TelegramController
     - Spec: 3 sentences. Pattern: visible in WhatsAppController.
     - Classification: Sonnet.

  C. Map Telegram message format to internal Message entity
     - Spec: needs decision on how to handle Telegram-only fields.
     - Classification: Opus (design decision).

  D. Wire TelegramModule into AppModule
     - Spec: 1 sentence. Pattern: obvious.
     - Classification: Codex.

  E. Integration tests for webhook → message persistence
     - Spec: 2 sentences. Pattern: copy structure from WhatsApp tests.
     - Classification: Codex.

Dependencies:
  B depends on A
  C depends on A
  D depends on A
  E depends on B, C, D

Pipeline:
  Stage 1: A (Codex)
  Stage 2: B (Sonnet) ∥ C (Opus) ∥ D (Codex)   ← parallel
  Stage 3: E (Codex)
  Stage 4: Opus review + commit
```

**Layer 2, Sonnet orchestrator** runs this pipeline mechanically.

**Layer 3, execution** happens with the right tool for each subtask. C escalates back to Opus orchestrator if Sonnet's confidence drops; A/D/E are dispatched via `codex-delegate` and their diffs are collected.

**Layer 4, Opus review** reads the combined diff, runs the gates (lint, tests, build), approves the commit.

---

## Non-negotiables

- **The orchestrator commits, never a subagent.** Especially not Codex (its sandbox cannot reliably write `.git`).
- **Run the classifier on every subtask, no shortcuts.** "Looks simple" is not a classification.
- **Subagent self-reports are claims, not evidence.** Re-run the project's gates in Layer 4 yourself.
- **Opus is for thinking, not typing.** If you are using Opus to scaffold a module or write boilerplate, you are doing it wrong, that work goes to Codex.
- **Parallel requires independence.** If two subtasks need each other's output, they belong in different pipeline stages.

---

## Anti-patterns

- Opus-as-orchestrator throughout (most common waste).
- Classifying every task as "complex" out of caution → Opus everywhere by default.
- Skipping Layer 4 because "the subagents said it passed."
- Running 5 things in parallel that actually have dependencies → they fail and you redo.
- Writing a Codex brief that says "figure it out" → Codex needs explicit specs.

---

## Quick reference card

```
1. Plan       (Opus,   once) → use superpowers:writing-plans for structure,
                               then enrich every step with:
                                 • classification (Codex/Sonnet/Opus)
                                 • explicit dependencies
                                 • pipeline stage assignment
2. Orchestrate (Sonnet)      → dispatch + collect + sequence + handle escalation
3. Execute    (mixed)        → Codex (mechanical) / Sonnet (standard) / Opus (complex)
                               parallel WITHIN stages, sequence ACROSS stages
4. Review     (Opus,   once) → diff + gates + scope check + commit
```

3-question classifier:

```
Q1: Spec in 3 sentences?       yes → Codex/Sonnet    no → Q2
Q2: Pattern obvious from code? yes → Sonnet          no → Q3
Q3: Needs design/debug call?   yes → Opus            no → re-check Q2
```

Escalation rule:

```
Sonnet/Codex unsure → escalate to Opus subagent
Opus unsure         → escalate to user
```
