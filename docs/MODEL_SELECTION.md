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
`ANTHROPIC_API_KEY` environment variable (set in `.env` or shell).

**Actual cost per run** (based on observed token usage ~8k–15k tokens):

| Tokens | Input cost ($3/M) | Output cost ($15/M) | Total |
|--------|-------------------|---------------------|-------|
| 8k (light run) | $0.000024 | $0.00015 | ~$0.0002 |
| 12k (typical) | $0.000036 | $0.00023 | ~$0.0003 |
| 15k (with skills) | $0.000045 | $0.00028 | ~$0.0003 |

**Real-world estimate: $0.001–$0.005 per lease analysis** — well under a cent
for most runs. The previous estimate of $0.01–$0.05 was 10–50x too high.

## Switching models

The `--frontier` flag switches from Granite to Claude. The agent loop
(`agentkit/loop.py`) detects the model name and routes to the appropriate
backend automatically.

Model detection logic:
- Contains "granite", "llama", "mistral", "qwen", or ":" → Ollama
- Otherwise → Anthropic Claude

## Cost tracking

Every run logs `cost_usd` to `logs/runs.jsonl`. The cost formula in
`agentkit/loop.py`:

```python
cost = (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
```

Granite runs are always `$0.00` (local, no API).
