import json
import re
import os
import requests

from .tools import TOOLS
from .prompts import SYSTEM_PROMPT


OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

def _call_ollama(messages: list[dict]) -> str:
    """
    POST to Ollama /api/chat (OpenAI-compatible messages format).

    Args:
        messages: list of {"role": "system"|"user"|"assistant", "content": str}

    Returns:
        The assistant reply as a plain string.

    Raises:
        RuntimeError if Ollama is unreachable or returns an error.
    """
    payload = {
        "model":    OLLAMA_MODEL,
        "messages": messages,
        "stream":   False,
        "options": {
            "temperature": 0.7,
            "num_predict": 512,   # max tokens per reply — keeps responses concise
        },
    }
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120,   # local inference can take a few seconds
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure it's running:\n"
            "    ollama serve\n"
            "Then try again."
        )
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama returned an error: {exc}") from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOOL_CALL_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)


def _extract_tool_calls(text: str) -> list[dict]:
    """
    Parse all <tool_call>...</tool_call> blocks from a model reply.

    Returns a list of dicts like:
        [{"name": "analyze_emotion", "arguments": {"text": "..."}}]
    """
    calls = []
    for raw in _TOOL_CALL_RE.findall(text):
        try:
            calls.append(json.loads(raw.strip()))
        except json.JSONDecodeError as exc:
            print(f"[agent_loop] Malformed tool_call JSON skipped: {exc}")
    return calls


def _strip_tool_calls(text: str) -> str:
    """Remove <tool_call> blocks so the user never sees raw JSON."""
    return _TOOL_CALL_RE.sub("", text).strip()


def _history_to_messages(history: list[dict]) -> list[dict]:
    """
    Convert our internal history format → Ollama messages format.

    Internal:  [{"role": "user"|"model", "parts": ["text"]}]
    Ollama:    [{"role": "user"|"assistant", "content": "text"}]
    """
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for entry in history:
        role = "assistant" if entry["role"] == "model" else entry["role"]
        text = entry["parts"][0] if isinstance(entry["parts"][0], str) \
               else entry["parts"][0].get("text", "")
        msgs.append({"role": role, "content": text})
    return msgs


# Main agent function
def run_agent(
    user_message:    str,
    history:         list[dict],
    user_id:         str = "default_user",
    max_tool_rounds: int = 3,
) -> tuple[str, list[dict], list[dict]]:
    """
    Run one turn of the MindEase agent loop (Ollama-backed).

    Args:
        user_message:    The latest message from the user.
        history:         Conversation history:
                         [{"role": "user"|"model", "parts": ["text"]}]
        user_id:         Used to tag mood journal entries.
        max_tool_rounds: Safety cap on tool-call iterations.

    Returns:
        (final_reply, updated_history, tool_log)
    """
    tool_log: list[dict] = []

    # Build the full message list for Ollama (system + history + new user msg)
    messages = _history_to_messages(history)
    messages.append({"role": "user", "content": user_message})

    # ── Round 1: LLM decides what to do (may embed <tool_call> tags) ──────────
    reply = _call_ollama(messages)
    messages.append({"role": "assistant", "content": reply})

    # Track internally
    history = history + [{"role": "user", "parts": [user_message]}]

    # ── Fallback nudge: if model forgot to call tools, remind it explicitly ───
    if not _extract_tool_calls(reply):
        nudge = (
            "You forgot to call the tools. "
            "The user shared an emotional state. "
            "Please call analyze_emotion, get_coping_strategy, search_music, and log_mood now "
            "using the <tool_call> format shown in your instructions. "
            "Output ONLY the tool call tags, nothing else."
        )
        messages.append({"role": "user", "content": nudge})
        reply = _call_ollama(messages)
        messages.append({"role": "assistant", "content": reply})
        print("  ↩ Nudged model to call tools")

    # ── Tool-call loop ─────────────────────────────────────────────────────────
    for _round in range(max_tool_rounds):
        calls = _extract_tool_calls(reply)
        if not calls:
            break

        tool_result_lines: list[str] = []

        for call in calls:
            tool_name = call.get("name", "")
            tool_args = call.get("arguments", {})

            # Auto-inject user_id so the LLM doesn't need to track it
            if tool_name == "log_mood" and "user_id" not in tool_args:
                tool_args["user_id"] = user_id

            if tool_name not in TOOLS:
                tool_result_lines.append(f"[Tool '{tool_name}'] Error: not found.")
                continue

            try:
                result     = TOOLS[tool_name](**tool_args)
                result_str = json.dumps(result, ensure_ascii=False)
                tool_log.append({"tool": tool_name, "args": tool_args, "result": result})
                tool_result_lines.append(f"[Tool: {tool_name}] Result: {result_str}")
                print(f"  ✓ {tool_name} → {result_str[:120]}")
            except Exception as exc:
                err = f"[Tool: {tool_name}] Error: {exc}"
                tool_result_lines.append(err)
                print(f"  ✗ {err}")

        # Feed tool results back → LLM synthesises a natural reply
        feedback = (
            "Here are the tool results. "
            "Write a warm, natural reply for the user. "
            "Do NOT mention tool names or raw JSON.\n\n"
            + "\n".join(tool_result_lines)
        )
        messages.append({"role": "user", "content": feedback})
        reply = _call_ollama(messages)
        messages.append({"role": "assistant", "content": reply})

    final_reply = _strip_tool_calls(reply)
    history     = history + [{"role": "model", "parts": [final_reply]}]

    return final_reply, history, tool_log
