# MindEase — LLM-Powered Mental Wellness Agent

An agent that runs entirely on your local machine. It listens to how you feel, calls four specialised tools to understand your emotion, retrieve a coping strategy, find a mood-matched song from iTunes, and log the session to a private journal — then weaves all of that into a single warm reply.

---

## Architecture

```
User (Gradio UI)
      │
      ▼
 Agent Loop  ◄──────────────────────────────┐
 (agent_loop.py)                            │
      │                                     │
      ▼                                     │
 Ollama / llama3.1:8b  ──► <tool_call>      │
                               │            │
          ┌────────────────────┼────────────┘
          │                    │
    ┌─────┴──────┐    ┌────────┴───────┐
    │            │    │                │
  Tool 1       Tool 2  Tool 3        Tool 4
analyze_     get_coping  search_      log_mood
emotion      _strategy   music        (SQLite)
(HuggingFace (local JSON) (iTunes API)
  API)
```

### The Four Tools

| # | Tool | Backend | Free? |
|---|------|---------|-------|
| 1 | `analyze_emotion` | HuggingFace Inference API + keyword fallback | Yes |
| 2 | `get_coping_strategy` | Local JSON knowledge base | Yes |
| 3 | `search_music` | iTunes Search API (no key required) | Yes |
| 4 | `log_mood` | Local SQLite file | Yes |

`search_music` is the dynamic tool. It calls the live iTunes Search API, parses the JSON response, selects the best track for the user's emotional state, and returns an audio and album artwork.

---

## Local Setup

### What you need

- Python 3.10 or newer
- [Ollama](https://ollama.com) installed and running

### Step by step

```bash
# 1. Download the model once (~5 GB, stored globally in ~/.ollama/models/)
ollama pull llama3.1:8b

# 2. Start the Ollama server — keep this terminal open
ollama serve

# 3. In a new terminal, set up the project
git clone https://github.com/YOUR_USERNAME/mental-health-agent.git
cd mental-health-agent
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows

# 4. Install dependencies (just two packages)
pip install -r requirements.txt

# 5. Run the app
python app.py
# Open http://localhost:7860
```

Optional: set a HuggingFace token to improve emotion detection accuracy.

```bash
export HF_TOKEN=your_token_here
```

### Run the evaluation suite

```bash
python eval/evaluate.py
# Results saved to eval/eval_results.json
```

---

## Evaluation

Three metrics are measured across 10 annotated test cases:

| Metric | What it measures |
|--------|-----------------|
| Tool Call Recall | Whether the agent called all expected tools for each scenario |
| Emotion Accuracy | Whether `analyze_emotion` matched the hand-labelled ground truth |
| LLM-as-Judge | The local model rates each reply 1 to 5 for empathy and usefulness |

Results from the included run: **97.5% tool recall, 70% emotion accuracy, 4.0 average quality score.**

---

## Project Structure

```
mental-health-agent/
├── agent/
│   ├── agent_loop.py     # Hand-written Plan → Tool → Respond loop
│   ├── tools.py          # All four tools
│   └── prompts.py        # System prompt with few-shot examples
├── data/
│   ├── strategies.json   # Coping strategy knowledge base
│   └── journal.db        # SQLite mood journal (auto-created on first run)
├── eval/
│   ├── test_cases.json   # 10 annotated test cases
│   ├── evaluate.py       # Evaluation script
│   └── eval_results.json # Latest results
├── app.py                # Gradio UI (port 7860)
└── requirements.txt
```

---

## Design Decisions

**Local model over cloud API.** Ollama keeps everything on-device with no quota limits and no user data leaving the machine — which matters for a mental wellness context.

**No agent framework.** The loop in `agent_loop.py` is plain Python. This makes the tool-call format, retry behaviour, and nudge mechanism easy to inspect and customise.

**Dynamic music tool.** Rather than returning a static script, `search_music` calls the iTunes API on every turn and returns a real, playable song. This demonstrates live JSON parsing and is the most distinctive feature of the agent.

**Few-shot system prompt.** Local 8B models respond much more reliably to explicit examples than to abstract instructions, so `prompts.py` includes a complete worked example of the expected tool-call format.
