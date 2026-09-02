# Example: Migrating a Flutter App from `StatefulWidget` to Hooks

An illustrative walkthrough of applying `zak-delegator` to a mechanical, codebase-wide migration in a Flutter app. (Presented as a worked thought-experiment, your actual run will produce different file lists and a different judgement-call distribution, but the shape will look like this.)

**Context.** A mid-size Flutter app uses `StatefulWidget` throughout. The team has decided to migrate to `flutter_hooks` for ergonomics. ~40 widgets are affected.

This is the scenario `zak-delegator` is best at: a high-volume, mechanical change with a small number of judgement calls hidden in the pile.

---

## Layer 1: Planning (Opus, once)

```markdown
## Step 1: Inventory and triage
- Acceptance: A list of every StatefulWidget in lib/, classified
  into:
    A) Pure conversion (only setState, no lifecycle hooks)
    B) Mechanical conversion (uses didChangeDependencies,
       initState, dispose)
    C) Needs human judgement (subclasses something, uses
       GlobalKey, uses Ticker, etc.)
- Testing: The inventory file builds without error.
- Classification: Sonnet (analysis, no implementation).
- Dependencies: none.
- Pipeline stage: 1.

## Step 2: Convert all Group A widgets
- Acceptance: Every Group-A widget compiles, original tests pass.
- Testing: dart analyze + flutter test on affected files.
- Classification: Codex (purely mechanical, identical pattern).
- Dependencies: Step 1.
- Pipeline stage: 2.

## Step 3: Convert all Group B widgets
- Acceptance: Every Group-B widget compiles, original tests pass.
- Testing: dart analyze + flutter test on affected files.
- Classification: Codex (mechanical but pattern-aware, useEffect
  / useState / dispose mapping).
- Dependencies: Step 1.
- Pipeline stage: 2.

## Step 4: Resolve Group C widgets case-by-case
- Acceptance: For each Group-C widget, either a converted version
  with rationale, OR an explicit deferral with reason.
- Testing: dart analyze + flutter test on affected files.
- Classification: Opus (real judgement calls).
- Dependencies: Step 1.
- Pipeline stage: 2.

## Step 5: Refresh the BLoC test harness
- Acceptance: All widget tests run green against the new hook-
  based widgets.
- Testing: flutter test.
- Classification: Sonnet (clear pattern, but touches test
  scaffolding).
- Dependencies: Steps 2, 3, 4.
- Pipeline stage: 3.

## Step 6: Remove the now-unused StatefulWidget imports
- Acceptance: dart analyze reports zero unused-import warnings.
- Testing: dart analyze.
- Classification: Codex (removal sweep, mechanical).
- Dependencies: Step 5.
- Pipeline stage: 4.
```

**Dependency graph.**

```
Step 1 ──┬── Step 2 ──┐
         ├── Step 3 ──┼── Step 5 ── Step 6
         └── Step 4 ──┘
```

**Pipeline.**

```
Stage 1: Step 1
Stage 2: Step 2 || Step 3 || Step 4
Stage 3: Step 5
Stage 4: Step 6
Stage 5: Layer 4 review + commit
```

---

## Layer 2: Orchestration (Sonnet)

The orchestrator dispatches:

- **Step 1**: a Sonnet subagent that produces the inventory file (`migration_inventory.md`) with three lists.
- **Stage 2** (parallel): a Codex job for Group A, a Codex job for Group B, an Opus subagent for Group C.
- **Step 5**: a Sonnet subagent updating the test harness.
- **Step 6**: a Codex job sweeping unused imports.

---

## Layer 3: Execution highlights

**Step 2 (Codex on Group A).** Brief includes: the list of files, the target pattern (a worked before/after on one file), the gate commands (`dart analyze`, `flutter test`), and the explicit instruction "convert exactly these files, do not touch anything else."

**Step 3 (Codex on Group B).** Similar, with the worked before/after showing how `initState` maps to `useEffect(() { ... return null; }, [])` and `dispose` collapses into the cleanup return.

**Step 4 (Opus on Group C).** The brief here is *open*. Opus is expected to make judgement calls: a widget that subclasses a custom base class might not be a good hook conversion candidate at all. The deliverable can include "this widget should not be migrated, because X", that is a valid Step 4 outcome and a valuable signal from the planning round.

---

## Layer 4: Review (Opus, once)

Opus reads the combined diff and verifies:

- Every file in the inventory was either converted or explicitly deferred (with reason).
- No new behaviour was introduced, every conversion is a pure shape change.
- The Step-4 judgement calls have reasoning attached, not just blind conversion.

If clean, the human commits. Likely several commits, grouped by stage:

1. `chore(migration): add hook migration inventory`
2. `refactor: convert Group A widgets to hooks`
3. `refactor: convert Group B widgets to hooks`
4. `refactor: convert Group C widgets (with deferrals)`
5. `test: refresh widget tests for hook-based widgets`
6. `chore: remove unused StatefulWidget imports`

---

## What this example demonstrates

- **Volume × mechanical = Codex's sweet spot.** Group A + Group B + Step 6 are exactly the work Codex does well.
- **Routing reveals hidden complexity.** Group C looks like "more of the same" but is actually where real decisions live. Surfacing it as an Opus task in Layer 1 prevents the entire migration from drifting into "Sonnet guesses, you patch later."
- **Sonnet handles the seams.** Inventory (Step 1) and test refresh (Step 5) need light reasoning but no design, Sonnet's lane.
- **Layer 4 catches the silent failures.** A Codex job that "looks done" might have skipped a file the brief was too vague about. Re-running `dart analyze` on the full project is non-negotiable.
