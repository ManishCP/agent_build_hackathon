# Model Selection Guide

## Local model: granite4:micro (default)

**Use for:** Development, testing, fast iteration, offline use.

```bash
python agent.py lease.txt
```

Granite 4 Micro runs locally via Ollama. It supports tool calling and is
fast enough for interactive development. Quality is lower than frontier
models but sufficient for structured analysis tasks with good skill context.

**Requirements:**
- Ollama installed and running
- `ollama pull granite4:micro` executed

## Frontier model: claude-sonnet-4-6

**Use for:** Production runs, eval benchmarks, highest-quality analysis.

```bash
python agent.py lease.txt --frontier
```

Claude Sonnet 4.6 provides the best analysis quality. Requires an
`ANTHROPIC_API_KEY` environment variable.

**Cost:** Approximately $0.01–0.05 per lease analysis.

## Switching models

The `--frontier` flag switches from Granite to Claude. The agent loop
(`agentkit/loop.py`) detects the model name and routes to the appropriate
backend automatically.

Model detection logic:
- Contains "granite", "llama", "mistral", "qwen", or ":" → Ollama
- Otherwise → Anthropic Claude
