# Example: Adding a Telegram Channel to a NestJS Backend

An illustrative walkthrough of applying `zak-delegator` to a realistic feature in a multi-channel NestJS API. (It's modelled on real work but presented as a worked thought-experiment, not a literal transcript.)

**Context.** A backend (in my case, an Arabic-first multi-channel messaging SaaS) already supports WhatsApp as a messaging channel. We want to add Telegram as a parallel channel, reusing the existing message-handling architecture.

---

## Layer 1: Planning (Opus, once)

A single Opus pass produces this plan. Note how each step carries the routing metadata Layer 2 needs.

```markdown
## Step 1: Scaffold the TelegramModule
- Acceptance: Module compiles, registered in AppModule, exposes
  empty TelegramController and TelegramService.
- Testing: Module instantiates in the test bed.
- Classification: Codex (mechanical scaffold; pattern identical
  to WhatsAppModule).
- Dependencies: none.
- Pipeline stage: 1.

## Step 2: Implement the Telegram webhook receiver
- Acceptance: POST /telegram/webhook accepts Telegram update
  payloads and returns 200.
- Testing: Integration test with a sample Telegram update.
- Classification: Sonnet (standard endpoint; pattern visible in
  WhatsAppController).
- Dependencies: Step 1.
- Pipeline stage: 2.

## Step 3: Map Telegram message format to the internal Message entity
- Acceptance: Conversion preserves text, sender id, timestamp,
  and reply context. Decisions captured for Telegram-specific
  fields (entities, inline keyboards).
- Testing: Unit tests over a battery of sample payloads.
- Classification: Opus (requires design decisions on how to
  represent Telegram-only fields in a channel-agnostic entity).
- Dependencies: Step 1.
- Pipeline stage: 2.

## Step 4: Wire TelegramModule into AppModule
- Acceptance: Module loads at app boot, no DI errors, /telegram
  routes are reachable.
- Testing: Existing e2e suite still passes.
- Classification: Codex (one-line wiring, pattern obvious).
- Dependencies: Step 1.
- Pipeline stage: 2.

## Step 5: Integration tests for webhook → persistence
- Acceptance: A simulated Telegram webhook ends as a Message row
  in the test DB.
- Testing: Itself.
- Classification: Codex (mechanical; pattern visible in WhatsApp
  integration tests).
- Dependencies: Steps 2, 3, 4.
- Pipeline stage: 3.
```

**Dependency graph.**

```
Step 1 ──┬── Step 2 ──┐
         ├── Step 3 ──┼── Step 5
         └── Step 4 ──┘
```

**Pipeline.**

```
Stage 1: Step 1
Stage 2: Step 2 || Step 3 || Step 4   (all parallel after Step 1)
Stage 3: Step 5
Stage 4: Layer 4 review + commit
```

---

## Layer 2: Orchestration (Sonnet)

Sonnet executes the pipeline mechanically. No design decisions; just dispatch and collect.

```
Stage 1
  └─ Step 1 → dispatch to Codex (codex-delegate skill)
      └─ wait for completion → run quick gate check

Stage 2 (parallel)
  ├─ Step 2 → Sonnet subagent
  ├─ Step 3 → Opus subagent
  └─ Step 4 → Codex
      └─ wait for all three → run quick gate check

Stage 3
  └─ Step 5 → Codex
      └─ wait for completion → run quick gate check
```

The orchestrator embeds the same instruction in every subagent's brief:

> "If you are less than 90% confident in your approach, stop and report what you are unsure about. Do not guess."

---

## Layer 3: Execution (mixed)

**Step 1, Step 4, Step 5** go through `codex-delegate`. The orchestrator writes a focused brief for each (the goal, the file pattern to follow from the WhatsApp module, the gate commands), and Codex returns a diff in its sandbox.

**Step 2** runs in a Sonnet subagent. The implementation pattern is visible in `WhatsAppController`, so reasoning load is low.

**Step 3** runs in an Opus subagent. It involves a design call (how to store Telegram-only fields without polluting the channel-agnostic schema). Sonnet would either guess or escalate; routing it to Opus from the start saves the escalation round-trip.

---

## Layer 4: Review (Opus, once)

Opus reads the combined diff, runs `npm run lint && npm test && npm run build` and confirms:

- Every changed file maps back to a step's acceptance criteria.
- No scope drift: nothing was added that the briefs did not ask for.
- The Telegram-specific fields decision from Step 3 is captured in code comments and matches what was proposed in planning.

If clean, the orchestrator hands the final summary to the human. The human runs `git commit` themselves.

---

## What this example demonstrates

- **Routing pays off.** Two of five steps would be wasted Opus tokens under an Opus-everywhere pattern. Three of five would be brittle under a Sonnet-everywhere pattern.
- **Parallelism is real.** Stage 2 collapses three parallel paths into one wall-clock unit.
- **The classifier earned its name on Step 3.** "It's just a mapping function" is the kind of thing that looks Sonnet-tier but is actually Opus-tier because of the embedded design decision.
- **Codex did the typing**, not the thinking. Briefs for Codex are tight; briefs for Opus are open-ended.
