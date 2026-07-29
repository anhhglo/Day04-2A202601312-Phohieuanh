"""The fixed agent loop. Students do NOT write this — it is the same for
everybody so that grading compares prompts and tool contracts, not loops.

Errors are always returned to the model AS DATA (never raised through the
loop), and the loop is hard-capped at MAX_ROUNDS.
"""

import json
import traceback

from . import providers
from .providers import ProviderError
from .tools import ToolContext

MAX_ROUNDS = providers.MAX_ROUNDS
TOKEN_BUDGET = 3000


def run_agent(system_prompt, tools, tool_impls, user_message, provider):
    """Run one conversation. Returns a trace dict used by the grader."""
    trace = {
        "user": user_message,
        "calls": [],          # [{"name":..., "args":..., "result":...}]
        "answer": "",
        "tokens": 0,
        "rounds": 0,
        "hit_max_rounds": False,
        "crashed": None,
        "infra_error": None,     # provider/network failure, NOT the agent's fault
    }
    messages = [{"role": "user", "content": user_message}]

    try:
        for rnd in range(MAX_ROUNDS):
            trace["rounds"] = rnd + 1
            resp = provider(system_prompt, tools, messages)
            trace["tokens"] += int(resp.get("tokens") or 0)

            calls = resp.get("tool_calls") or []
            if not calls:
                trace["answer"] = resp.get("text") or ""
                break

            # Echo back every distinct assistant item that produced a call.
            # Providers differ: OpenAI's Responses API gives ONE function_call
            # item per call (all must be echoed, or the follow-up request 400s
            # because a function_call_output has no matching call), while
            # Anthropic/chat-completions hand back a single object shared by
            # every call in the turn. Dedupe by identity to satisfy both.
            echoed = []
            for call in calls:
                raw = call.get("raw")
                if raw is None or any(raw is e for e in echoed):
                    continue
                echoed.append(raw)
                messages.append({"role": "assistant_call", "raw": raw})

            for i, call in enumerate(calls):
                name = call.get("name")
                args = call.get("args") or {}
                fn = tool_impls.get(name)
                if fn is None:
                    result = {"status": "error",
                              "message": f"No such tool: {name}",
                              "code": "TOOL_NOT_FOUND"}
                else:
                    try:
                        result = fn(**args)
                    except TypeError as e:
                        result = {"status": "error",
                                  "message": f"Bad arguments: {e}",
                                  "code": "BAD_ARGS"}
                    except Exception as e:            # noqa: BLE001
                        result = {"status": "error", "message": str(e),
                                  "code": "TOOL_EXCEPTION"}

                trace["calls"].append({"name": name, "args": args,
                                       "result": result})
                messages.append({
                    "role": "tool",
                    "call_id": call.get("call_id", f"call_{rnd}_{i}"),
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            trace["hit_max_rounds"] = True
    except ProviderError as e:
        # The model call never succeeded. Scoring this as an agent failure
        # would rank the student on API weather.
        trace["infra_error"] = str(e)
    except Exception:                                  # noqa: BLE001
        trace["crashed"] = traceback.format_exc(limit=3)

    return trace
