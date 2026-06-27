"""
Local agentkit shim — provides get_client.
"""
from pathlib import Path
import os

# Load .env from project root (no external library needed)
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        if _line.strip() and not _line.startswith("#") and "=" in _line:
            _key, _val = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _val.strip())


def get_client(model: str = "granite4:micro"):
    """Return an LLM client for the given model."""
    if "granite" in model or ":" in model:
        import ollama
        return ollama.Client()
    else:
        import anthropic
        return anthropic.Anthropic()
