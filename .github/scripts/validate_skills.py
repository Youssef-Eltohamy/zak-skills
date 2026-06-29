#!/usr/bin/env python3
"""Validate every skills/*/SKILL.md in the repo.

A SKILL.md is valid if it:
  - exists at skills/<name>/SKILL.md
  - has YAML frontmatter delimited by ---
  - declares a non-empty `name` and `description` field
  - the directory name matches the `name` field
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_value_lines: list[str] = []
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith(" ") or line.startswith("\t"):
            if current_key is not None:
                current_value_lines.append(line.strip())
            continue
        if ":" in line:
            if current_key is not None:
                fields[current_key] = " ".join(current_value_lines).strip()
            key, _, value = line.partition(":")
            current_key = key.strip()
            current_value_lines = [value.strip().lstrip(">").strip()]
    if current_key is not None:
        fields[current_key] = " ".join(current_value_lines).strip()
    return fields


def validate(repo_root: Path) -> int:
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        print(f"::error::skills/ directory not found at {skills_dir}")
        return 1

    errors: list[str] = []
    skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
    if not skill_dirs:
        print("::error::No skills found under skills/")
        return 1

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill_dir.name}: SKILL.md not found")
            continue

        text = skill_md.read_text(encoding="utf-8")
        fields = parse_frontmatter(text)

        if not fields:
            errors.append(f"{skill_dir.name}: missing or malformed YAML frontmatter")
            continue
        if not fields.get("name"):
            errors.append(f"{skill_dir.name}: frontmatter missing `name`")
        elif fields["name"] != skill_dir.name:
            errors.append(
                f"{skill_dir.name}: frontmatter name `{fields['name']}` "
                f"does not match directory name"
            )
        if not fields.get("description"):
            errors.append(f"{skill_dir.name}: frontmatter missing `description`")
        elif len(fields["description"]) < 40:
            errors.append(
                f"{skill_dir.name}: description is suspiciously short "
                f"({len(fields['description'])} chars) — describe both *what* and *when*"
            )

        print(f"checked {skill_dir.name}")

    if errors:
        print("\nValidation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"\nAll {len(skill_dirs)} skill(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(validate(Path(__file__).resolve().parents[2]))
