# Lease Analyzer Agent

A commercial lease analysis agent built for TOA Agent Build Day 2026.

Analyzes commercial lease documents and produces a plain-English risk report
covering financial terms, legal clauses, exit flexibility, and negotiation asks.

## Quick start

```bash
# Install dependencies
pip install anthropic ollama

# Pull local model
ollama pull granite4:micro

# Analyze a lease file (local model)
python agent.py evals/files/sample_lease.txt

# Analyze with inline text
python agent.py --text "NNN lease at $8,500/mo with 4% escalation..."

# Use Claude (frontier)
export ANTHROPIC_API_KEY=your-key
python agent.py evals/files/sample_lease.txt --frontier

# Baseline run (no skill context)
python agent.py evals/files/sample_lease.txt --no-skill
```

## Project structure

```
lease-analyzer/
├── agent.py                    # Main agent entry point
├── agentkit/                   # Local shim (overrides installed agentkit)
│   ├── loop.py                 # run_agent, tool decorator, agent loop
│   └── llm.py                  # get_client for Ollama/Anthropic
├── skills/
│   ├── financial_risk/
│   │   ├── SKILL.md            # Domain knowledge for financial terms
│   │   └── scripts/
│   │       └── financial_checks.py
│   ├── clause_risk/
│   │   ├── SKILL.md            # Domain knowledge for legal clauses
│   │   └── scripts/
│   │       └── clause_checks.py
│   ├── exit_risk/
│   │   ├── SKILL.md            # Domain knowledge for exit terms
│   │   └── scripts/
│   │       └── exit_checks.py
│   └── negotiation_playbook/
│       ├── SKILL.md            # Negotiation synthesis instructions
│       └── assets/
│           └── negotiation_template.md
├── evals/
│   ├── evals.json              # Eval suite with assertions
│   └── files/
│       └── sample_lease.txt    # Sample NNN lease with multiple red flags
├── fixtures/
│   └── sample_inputs.json      # Structured test inputs
└── docs/
    ├── ADLC.md                 # Agent Development Lifecycle
    └── MODEL_SELECTION.md      # When to use local vs frontier
```

## Skills

Skills are SKILL.md files that inject domain knowledge into the model's
system prompt. Each skill covers one analysis area:

- **financial_risk**: NNN true cost, CAM caps, escalation benchmarks, deposit
- **clause_risk**: Personal guarantee, auto-renewal traps, subletting, entry rights
- **exit_risk**: Holdover trap, early termination, break clause, M&A assignment
- **negotiation_playbook**: Synthesizes all findings into a prioritized ask list

## Tools

The agent has three deterministic tools:

| Tool | Purpose |
|------|---------|
| `analyze_financial_terms` | Score NNN, CAM, escalation, deposit |
| `analyze_legal_clauses` | Score personal guarantee, auto-renewal, subletting |
| `analyze_exit_terms` | Score holdover, termination penalty, break clause |

## Evals

Three eval cases in `evals/evals.json`:
1. High-risk NNN lease (many red flags)
2. Tenant-friendly gross lease (minimal flags)
3. Clause-focused (personal guarantee + assignment + entry)

## License

MIT
