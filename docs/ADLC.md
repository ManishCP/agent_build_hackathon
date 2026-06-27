# Agent Development Lifecycle (ADLC)

This document describes the development lifecycle used for the lease-analyzer agent.

## Phases

### 1. Baseline (no-skill)
Run the agent without any skill context to establish a performance baseline.

```bash
python agent.py evals/files/sample_lease.txt --no-skill
```

### 2. Skill authoring
Write SKILL.md files in each skill directory. Skills encode domain knowledge
that would otherwise require the model to have memorized it.

### 3. Skill injection
Run the agent with skills loaded:

```bash
python agent.py evals/files/sample_lease.txt
```

### 4. Eval comparison
Compare baseline vs skill runs across the eval suite. Measure:
- Tool call accuracy (did it call all 3 tools?)
- Finding coverage (did it flag all expected issues?)
- Negotiation ask quality (are the asks specific and actionable?)

### 5. Iteration
Update SKILL.md files based on eval failures. Repeat until all assertions pass.

## Eval harness

Run all evals:
```bash
python -m pytest evals/ -v
```

Or manually using the prompts in `evals/evals.json`.
