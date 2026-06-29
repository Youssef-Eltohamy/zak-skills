# Contributing to zak-skills

PRs and issues welcome. This page is short on purpose — it's a one-author, one-skill repo today, and the bar should sound like that. If the collection grows, this file will too.

## What I'm looking for in a new skill

If you want to propose one, the things I care about:

- **A workflow opinion** that holds across projects and languages — not a snippet that happens to be reusable.
- **A failure mode it prevents.** A skill should answer "what would Claude do wrong without this?" in one sentence.
- **A clear when-to-use and when-not-to-use.** Skills that fire on everything fire usefully on nothing.

Things that don't fit here: code templates (use a template repo), thin CLI wrappers (use a script), MCP servers (different ecosystem), or prompt collections (those are notes).

## Proposing one

Open an issue first with a sketch of the skill — what it does, what it prevents, two tasks where it would apply. We can shape it before either of us spends real time.

A PR should include:

- `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`), under ~500 lines.
- `skills/<name>/USAGE.md` with ready-to-paste prompts.
- `skills/<name>/examples/` with at least one worked example.
- A row in the [Skills in this collection](README.md#skills-in-this-collection) table.

## Style

A few things I'll push back on in review:

- **Explain the why.** Today's Claude responds to reasoning better than to ALWAYS / NEVER. Skills that explain themselves age better.
- **Imperative voice.** "Run the gates yourself" beats "gates should be run".
- **No emojis in skill bodies.** They date the file. README badges are fine.
- **Keep SKILL.md tight.** Split into `references/` and link from the body if it grows past ~500 lines.

## How I review

I try the skill on a real task before merging. The bar:

- Did Claude behave differently with the skill loaded?
- Was the difference an improvement?
- Would I want this on by default?

## Local dev

```bash
git clone https://github.com/Youssef-Eltohamy/zak-skills.git
cd zak-skills

# Symlink your in-development skill into your Claude Code skills dir
ln -s "$(pwd)/skills/zak-delegator" ~/.claude/skills/zak-delegator
```

Iterate on `SKILL.md` and reload Claude Code to pick up changes.

## Code of conduct

Be respectful, assume good faith, keep critique on the work.
