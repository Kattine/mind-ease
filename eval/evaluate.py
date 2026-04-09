import json
import os
import sys
import time

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from agent.agent_loop import run_agent, OLLAMA_URL, OLLAMA_MODEL

TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.json")
RESULTS_PATH    = os.path.join(os.path.dirname(__file__), "eval_results.json")


def llm_judge(user_input: str, agent_reply: str) -> int:
    """
    Ask Gemini to rate the quality of the agent's reply on a 1–5 scale.

    Rubric:
        5 — Highly empathetic, actionable, warm tone.
        3 — Adequate but generic or shallow.
        1 — Off-topic, cold, or potentially harmful.

    Returns an integer 1–5 (defaults to 3 on parse failure).
    """
    prompt = (
        "You are an expert evaluator for mental wellness chatbots.\n\n"
        f'User said: "{user_input}"\n'
        f'Agent replied: "{agent_reply}"\n\n'
        "Rate this reply on a scale of 1 to 5:\n"
        "5 = Empathetic, warm, gives practical guidance\n"
        "3 = Acceptable but somewhat generic\n"
        "1 = Unhelpful, cold, or inappropriate\n\n"
        "Reply with a SINGLE digit only. No other text."
    )
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model":   OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream":  False,
                "options": {"temperature": 0, "num_predict": 4},
            },
            timeout=60,
        )
        text = resp.json()["message"]["content"].strip()
        # grab the first digit found
        for ch in text:
            if ch.isdigit() and ch != "0":
                return int(ch)
        return 3
    except Exception:
        return 3


def evaluate() -> None:
    with open(TEST_CASES_PATH, encoding="utf-8") as fh:
        cases = json.load(fh)

    results       = []
    tool_recall_total = 0.0
    emotion_hits      = 0
    judge_scores      = []

    divider = "=" * 64
    print(f"\n{divider}")
    print("  MindEase Agent — Evaluation Report")
    print(divider)

    for tc in cases:
        print(f"\n[{tc['id']}] {tc['input'][:55]}…")

        reply, _, tool_log = run_agent(
            user_message=tc["input"],
            history=[],
            user_id="eval_runner",
        )

        called_tools = [entry["tool"] for entry in tool_log]
        detected_emotion   = None
        detected_intensity = None

        for entry in tool_log:
            if entry["tool"] == "analyze_emotion":
                detected_emotion   = entry["result"].get("emotion")
                detected_intensity = entry["result"].get("intensity")
                break

        # ── Metric 1: Tool call recall ─────────────────────────────────────
        expected_set = set(tc["expected_tools"])
        called_set   = set(called_tools)
        recall       = (
            len(expected_set & called_set) / len(expected_set)
            if expected_set else 1.0
        )
        tool_recall_total += recall

        # ── Metric 2: Emotion detection accuracy ──────────────────────────
        emotion_correct = int(detected_emotion == tc["expected_emotion"])
        emotion_hits   += emotion_correct

        # ── Metric 3: LLM-as-Judge response quality ────────────────────────
        score = llm_judge(tc["input"], reply)
        judge_scores.append(score)

        # ── Per-case summary ───────────────────────────────────────────────
        emotion_icon = "✓" if emotion_correct else "✗"
        print(
            f"  Tools called : {called_tools}\n"
            f"  Tool recall  : {recall:.0%}  |  "
            f"Emotion: {emotion_icon} ({detected_emotion})  |  "
            f"Quality: {score}/5"
        )

        results.append({
            "id":              tc["id"],
            "input":           tc["input"][:80],
            "expected_emotion":  tc["expected_emotion"],
            "detected_emotion":  detected_emotion,
            "detected_intensity": detected_intensity,
            "expected_tools":  list(expected_set),
            "called_tools":    called_tools,
            "tool_recall":     round(recall, 3),
            "emotion_correct": bool(emotion_correct),
            "judge_score":     score,
            "reply_preview":   reply[:120],
        })

        time.sleep(0.5)  # Brief pause to avoid rate-limiting

    # ── Aggregate metrics ──────────────────────────────────────────────────────
    n           = len(cases)
    avg_recall  = tool_recall_total / n * 100
    avg_emotion = emotion_hits       / n * 100
    avg_judge   = sum(judge_scores)  / len(judge_scores)

    print(f"\n{'-' * 64}")
    print(f"  Summary (n={n} test cases)")
    print(f"{'-' * 64}")
    print(f"  Tool Call Recall        : {avg_recall:.1f}%")
    print(f"  Emotion Accuracy        : {avg_emotion:.1f}%")
    print(f"  LLM-as-Judge (avg)      : {avg_judge:.2f} / 5.0")
    print(f"{'-' * 64}\n")

    output = {
        "summary": {
            "n":                        n,
            "tool_recall_pct":          round(avg_recall,  1),
            "emotion_accuracy_pct":     round(avg_emotion, 1),
            "avg_judge_score":          round(avg_judge,   2),
        },
        "per_case": results,
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

    print(f"  Full results saved to: {RESULTS_PATH}\n")


if __name__ == "__main__":
    evaluate()
