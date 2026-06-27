"""
Local agentkit shim — provides get_client.
"""


def get_client(model: str = "granite4:micro"):
    """Return an LLM client for the given model."""
    if "granite" in model or ":" in model:
        import ollama
        return ollama.Client()
    else:
        import anthropic
        return anthropic.Anthropic()
