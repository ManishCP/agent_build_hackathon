"""
Local agentkit shim — provides run_agent and tool decorator.
Supports Ollama (local) and Anthropic Claude (frontier) models.
"""

import time
import json
import inspect
import functools
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class AgentResult:
    answer: str
    turns: int = 0
    tool_calls: int = 0
    tokens: int = 0
    cost: float = 0.0
    latency: float = 0.0


def tool(func: Callable) -> Callable:
    """Decorator to mark a function as an agent tool."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper._is_tool = True
    return wrapper


def _build_tool_schema(func: Callable) -> dict:
    """Build Anthropic-compatible tool schema from a Python function."""
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    lines = [l.strip() for l in doc.split('\n')]

    # First non-empty line is description
    description = next((l for l in lines if l), func.__name__)

    # Parse per-param descriptions: "param_name: description text"
    param_docs = {}
    for line in lines:
        for pname in sig.parameters:
            if line.startswith(f"{pname}:"):
                param_docs[pname] = line[len(pname)+1:].strip()

    type_map = {
        "str": "string", "int": "integer",
        "float": "number", "bool": "boolean",
    }

    properties = {}
    required = []
    for pname, param in sig.parameters.items():
        ann = param.annotation
        if ann is inspect.Parameter.empty:
            jtype = "string"
        else:
            tname = ann.__name__ if hasattr(ann, "__name__") else str(ann)
            jtype = type_map.get(tname, "string")
        properties[pname] = {
            "type": jtype,
            "description": param_docs.get(pname, pname),
        }
        if param.default is inspect.Parameter.empty:
            required.append(pname)

    return {
        "name": func.__name__,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def _run_claude(task: str, tools: list, tool_schemas: list, tool_map: dict,
                system: str, model: str) -> AgentResult:
    """Run agent loop using Anthropic Claude."""
    import anthropic

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": task}]
    turns = 0
    tool_calls_count = 0
    total_input_tokens = 0
    total_output_tokens = 0

    # Anthropic tool format
    ant_tools = []
    for schema in tool_schemas:
        ant_tools.append({
            "name": schema["name"],
            "description": schema["description"],
            "input_schema": schema["input_schema"],
        })

    while True:
        turns += 1
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=ant_tools,
        )
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # Collect assistant message content
        assistant_content = []
        tool_use_blocks = []

        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                tool_use_blocks.append(block)

        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn" or not tool_use_blocks:
            # Extract final text answer
            answer = ""
            for block in response.content:
                if hasattr(block, "text"):
                    answer += block.text
            total_tokens = total_input_tokens + total_output_tokens
            # Rough cost estimate for claude-sonnet-4-6
            cost = (total_input_tokens * 3.0 + total_output_tokens * 15.0) / 1_000_000
            return AgentResult(
                answer=answer.strip(),
                turns=turns,
                tool_calls=tool_calls_count,
                tokens=total_tokens,
                cost=cost,
                latency=0.0,
            )

        # Execute tool calls
        tool_results = []
        for block in tool_use_blocks:
            tool_calls_count += 1
            func = tool_map.get(block.name)
            if func:
                try:
                    result = func(**block.input)
                except Exception as e:
                    result = json.dumps({"error": str(e)})
            else:
                result = json.dumps({"error": f"Unknown tool: {block.name}"})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result),
            })

        messages.append({"role": "user", "content": tool_results})


def _run_ollama(task: str, tools: list, tool_schemas: list, tool_map: dict,
                system: str, model: str) -> AgentResult:
    """Run agent loop using Ollama local model."""
    import ollama

    # Convert to Ollama tool format
    ollama_tools = []
    for schema in tool_schemas:
        ollama_tools.append({
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["input_schema"],
            },
        })

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]
    turns = 0
    tool_calls_count = 0
    total_tokens = 0

    while True:
        turns += 1
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=ollama_tools,
        )
        msg = response.message
        total_tokens += response.get("eval_count", 0) + response.get("prompt_eval_count", 0)

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

        if not msg.tool_calls:
            return AgentResult(
                answer=(msg.content or "").strip(),
                turns=turns,
                tool_calls=tool_calls_count,
                tokens=total_tokens,
                cost=0.0,
                latency=0.0,
            )

        # Execute tool calls
        for tc in msg.tool_calls:
            tool_calls_count += 1
            fname = tc.function.name
            fargs = tc.function.arguments or {}
            func = tool_map.get(fname)
            if func:
                try:
                    result = func(**fargs)
                except Exception as e:
                    result = json.dumps({"error": str(e)})
            else:
                result = json.dumps({"error": f"Unknown tool: {fname}"})
            messages.append({
                "role": "tool",
                "content": str(result),
            })


def run_agent(task: str, tools: list, skill: str = "", model: str = "granite4:micro") -> AgentResult:
    """
    Run an agent loop with the given task, tools, and model.

    Args:
        task: The user task / prompt
        tools: List of @tool-decorated functions
        skill: System context loaded from SKILL.md files
        model: Model name — 'granite4:micro' for local Ollama, 'claude-sonnet-4-6' for frontier
    Returns:
        AgentResult with .answer, .turns, .tool_calls, .tokens, .cost, .latency
    """
    start = time.time()

    tool_schemas = [_build_tool_schema(t) for t in tools]
    tool_map = {t.__name__: t for t in tools}

    system = (
        "You are a commercial lease analyzer. Your job is to carefully read commercial lease "
        "documents and produce a detailed plain-English risk report.\n\n"
        "For each analysis:\n"
        "1. Extract all financial terms (rent, escalation, CAM, deposit, lease type)\n"
        "2. Extract all legal clauses (personal guarantee, auto-renewal, subletting, entry rights)\n"
        "3. Extract all exit terms (early termination, holdover, break clause, assignment)\n"
        "4. Call ALL THREE analysis tools with the extracted values\n"
        "5. Synthesize findings into a clear risk report with negotiation asks\n\n"
        "If a value is not stated in the lease, use a conservative/unfavorable default and note it."
    )
    if skill:
        system += f"\n\n{skill}"

    is_ollama = ("granite" in model or "llama" in model or "mistral" in model
                 or "qwen" in model or ":" in model)

    try:
        if is_ollama:
            result = _run_ollama(task, tools, tool_schemas, tool_map, system, model)
        else:
            result = _run_claude(task, tools, tool_schemas, tool_map, system, model)
    except Exception as e:
        result = AgentResult(answer=f"Error running agent: {e}")

    result.latency = time.time() - start
    return result
