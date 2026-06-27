#!/usr/bin/env python3
"""
Local skills-ref validator — checks agentskills.io spec compliance.
Usage: python scripts/validate_skills.py
"""
import re
import sys
from pathlib import Path

SKILL_DIRS = [
    "skills/financial_risk",
    "skills/clause_risk",
    "skills/exit_risk",
    "skills/negotiation_playbook",
]


def validate_skill(skill_dir: str) -> list[str]:
    errors = []
    p = Path(skill_dir)

    if not p.exists():
        return [f"FAIL: Directory not found: {skill_dir}"]

    skill_md = p / "SKILL.md"
    if not skill_md.exists():
        return [f"FAIL: SKILL.md not found in {skill_dir}"]

    content = skill_md.read_text()

    if not content.startswith("---"):
        errors.append("FAIL: No YAML frontmatter (must start with ---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("FAIL: Malformed frontmatter")
        return errors

    frontmatter = parts[1]

    # Check name field
    name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
    if not name_match:
        errors.append("FAIL: Missing required 'name' field")
    else:
        name = name_match.group(1).strip().strip('"\'')
        if len(name) > 64:
            errors.append(f"FAIL: name '{name}' exceeds 64 characters")
        if re.search(r'[^a-z0-9-]', name):
            errors.append(f"FAIL: name '{name}' contains invalid characters (only lowercase, numbers, hyphens)")
        if name.startswith('-') or name.endswith('-'):
            errors.append(f"FAIL: name '{name}' cannot start or end with hyphen")
        if '--' in name:
            errors.append(f"FAIL: name '{name}' cannot contain consecutive hyphens")
        # Warn if name doesn't match directory (underscore vs hyphen is OK)
        dir_name = p.name
        expected = dir_name.replace('_', '-')
        if name != expected:
            errors.append(f"WARN: name '{name}' does not match directory '{dir_name}' (expected '{expected}')")

    # Check description field
    desc_match = re.search(r'^description:\s*(.+?)(?=\n\w|\Z)', frontmatter, re.MULTILINE | re.DOTALL)
    if not desc_match:
        errors.append("FAIL: Missing required 'description' field")
    else:
        desc = desc_match.group(1).strip().strip('"\'').strip('|>').strip()
        if len(desc) == 0:
            errors.append("FAIL: description is empty")
        if len(desc) > 1024:
            errors.append(f"FAIL: description exceeds 1024 characters ({len(desc)} chars)")

    # Check license field
    if 'license:' not in frontmatter:
        errors.append("WARN: Missing 'license' field (recommended)")

    # Check body
    body = parts[2].strip()
    if len(body) < 50:
        errors.append("WARN: SKILL.md body is very short — add instructions, gotchas, output template")

    lines = body.split('\n')
    if len(lines) > 500:
        errors.append(f"WARN: Body is {len(lines)} lines — spec recommends under 500 lines")

    if not errors:
        errors.append("PASS")

    return errors


def main():
    print("\n" + "=" * 60)
    print("skills-ref validate — agentskills.io spec check")
    print("=" * 60 + "\n")

    all_passed = True
    for skill_dir in SKILL_DIRS:
        results = validate_skill(skill_dir)
        passed = all(r.startswith("PASS") or r.startswith("WARN") for r in results)
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False

        print(f"{status}  {skill_dir}/SKILL.md")
        for r in results:
            if not r.startswith("PASS"):
                print(f"       {r}")

    print("\n" + "=" * 60)
    if all_passed:
        print("All skills valid ✓")
    else:
        print("Some skills have errors — fix before submitting")
    print("=" * 60 + "\n")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
