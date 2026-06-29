# zak-delegator — Usage Guide

A practical reference of ready-to-paste prompts for using the `zak-delegator` skill in any Claude Code session.

---

## Step 1 — Brand new task (before brainstorming)

Use this when you don't have specs yet. Naming both skills tells Claude to load them; describing the workflow gives the trigger something concrete to match.

**Prompt:**

```
I have a new task to work on. I want to use the zak-delegator
pattern, but we're not at planning yet — first brainstorm
requirements with me (use the superpowers brainstorming skill),
then write the specs. Once specs are done, pause and wait for
my signal before producing the implementation plan.
```

---

## Step 2 — Specs are done (the critical step)

This is where the difference shows. The implementation plan that comes out of this step carries everything Layer 2 needs to execute mechanically.

**Prompt:**

```
The specs are finalised. Use zak-delegator + superpowers:writing-plans.

Produce an implementation plan in Layer-1 form:
  - atomic subtasks (one subtask = one brief = one commit)
  - explicit dependency graph (which subtask blocks which)
  - classification per subtask (Codex / Sonnet / Opus) using the
    3-question classifier
  - pipeline stages, with parallelism marked inside each stage

Go.
```

**Checklist before you proceed:**

- [ ] Every subtask carries an explicit `→ Codex` / `→ Sonnet` / `→ Opus` tag.
- [ ] Dependencies are written out, not implied by ordering.
- [ ] Subtasks are grouped into stages with parallelism marked.

If anything is missing:

```
The plan is missing [X]. Add it before we continue.
```

---

## Step 3 — Execute one stage

Run stages one at a time so you can validate before moving on.

**Prompt:**

```
Execute Stage [N] of the plan.

Use Sonnet as the orchestrator.
For each subtask in the stage, dispatch to the agent indicated by
its classification:
  - Codex tasks   → use the codex-delegate skill
  - Sonnet tasks  → subagent with model=sonnet
  - Opus tasks    → subagent with model=opus

Give every subagent this explicit instruction:
"If you are less than 90% confident, stop and report what you're
unsure about. Do not guess."

When all subagents return, give me a summary per subtask:
  - status (succeeded / failed / escalated)
  - what it actually did
  - which files changed
```

---

## Step 4 — After each stage (quick gate check)

Never move to a new stage before the previous one is clean.

**Prompt:**

```
Run the project's gates on the files that changed in Stage [N]:
  - lint
  - tests touching the affected files
  - type check if applicable

If any gate fails, fix it before we move to the next stage.
Do not commit this stage on its own.
```

---

## Step 5 — After the last stage (Layer 4 Review)

The final human checkpoint before commit.

**Prompt:**

```
All stages are complete. Run Layer 4 review:

1. Use Opus to read the full diff.
2. Run all project gates (do not trust subagent self-reports).
3. Scope check: each subagent did exactly what its brief asked
   for, nothing more (scope creep), nothing less.
4. Show me:
   - per-file diff summary
   - full gate results
   - any scope drift or unexpected change
   - a proposed commit message

I will take the commit decision.
```

---

## Common-problem prompts

### Problem 1 — A subagent escalated

**Prompt:**

```
The subagent on [task name] returned an escalation.
Spawn an Opus subagent to take over the same task with extra
context:
[describe the missing context or the decision that needs human
judgement]
```

### Problem 2 — A whole stage failed

**Prompt:**

```
Stage [N] failed. Do not continue the pipeline.
Diagnose the root cause:
  - Was the brief wrong?
  - Was the classification wrong (an Opus-grade task routed to
    Sonnet)?
  - Was a dependency missing from the original plan?
Propose a fix to the plan before we resume.
```

### Problem 3 — Codex returned a strange diff

**Prompt:**

```
The Codex diff for task [X] has [describe the issue].
Re-read the original brief, identify what was missing or
ambiguous, then use --resume-last in codex-delegate with a short
delta brief.
```

### Problem 4 — Gates failing in a confusing way

**Prompt:**

```
Gates failed after Stage [N] and I don't see the cause.
Run superpowers:systematic-debugging on the failure.
Do not start patching before the root cause is identified.
```

---

## Four golden rules

1. **Never enter a new stage before the previous one's gates pass.** Errors compound silently.
2. **One task = one commit.** Do not bundle unrelated work.
3. **Never intervene mid-stage.** If you feel the urge, wait for it to finish, then correct.
4. **You commit, always.** Never a subagent, never Codex, never even Opus.

---

## Performance notes

- **Don't run more than 3–4 parallel subagents at once.** The platform allows up to 16, but real throughput plateaus around 4–5 and quality of orchestration drops past that.
- **Codex is slower per task than Sonnet** but spends a different token bucket. For two adjacent mechanical tasks, send both to Codex in parallel.
- **If Layer 4 review finds scope drift**, send the offending task back to an *Opus* subagent with a tighter brief, not Sonnet. Scope drift usually means the original brief left too much room for interpretation.

---

## Where this file lives

After installing the skill:

```
~/.claude/skills/zak-delegator/USAGE.md
```

You can open it yourself, or ask Claude to consult it:

```
Read ~/.claude/skills/zak-delegator/USAGE.md and follow it.
```
