import gradio as gr
from agent.agent_loop import run_agent

# ---------------------------------------------------------------------------
# CSS — full design system
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Global reset & base ─────────────────────────────────────────── */
.gradio-container {
    background: #0f0e17 !important;
    font-family: 'DM Sans', sans-serif !important;
    max-width: 1280px !important;
    margin: 0 auto !important;
}

/* ── Header ──────────────────────────────────────────────────────── */
.mindease-header {
    text-align: center;
    padding: 48px 0 12px;
    position: relative;
}
.mindease-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 3rem !important;
    font-weight: 300 !important;
    color: #f2e9e4 !important;
    letter-spacing: 0.04em;
    margin: 0 0 6px !important;
    animation: breathe 6s ease-in-out infinite;
}
.mindease-subtitle {
    font-size: 0.95rem !important;
    color: #8b7e88 !important;
    font-weight: 300 !important;
    letter-spacing: 0.06em;
    margin: 0 !important;
}
@keyframes breathe {
    0%,100% { opacity: 0.9; }
    50%      { opacity: 1;   }
}

/* ── Status bar ──────────────────────────────────────────────────── */
.status-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin: 4px 0 20px;
    font-size: 0.78rem;
    color: #6b5e6a;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #c8956c;
    animation: pulse-dot 2.4s ease-in-out infinite;
    flex-shrink: 0;
}
@keyframes pulse-dot {
    0%,100% { opacity: 1; transform: scale(1);   }
    50%      { opacity: .5; transform: scale(.7); }
}

/* ── Chat panel ──────────────────────────────────────────────────── */
#chat-col {
    background: #16141f;
    border: 1px solid #2a2535;
    border-radius: 20px !important;
    padding: 0 !important;
    overflow: hidden;
}
#chatbot {
    height: 480px !important;
    background: transparent !important;
    border: none !important;
}
/* Chat bubbles — force light text on all children */
#chatbot .message.user,
#chatbot .message.user *,
#chatbot .message.user p,
#chatbot .message.user span {
    background: #2a1f35 !important;
    border: 1px solid #3d2e50 !important;
    color: #f0e8ff !important;
    border-radius: 18px 18px 4px 18px !important;
    font-size: 0.92rem !important;
}
#chatbot .message.bot,
#chatbot .message.bot *,
#chatbot .message.bot p,
#chatbot .message.bot span {
    background: #1c1728 !important;
    border: 1px solid #2e2540 !important;
    color: #d4c8e8 !important;
    border-radius: 18px 18px 18px 4px !important;
    font-size: 0.92rem !important;
}
/* Gradio 6 uses different class names — cover all variants */
#chatbot [data-testid="user"],
#chatbot [data-testid="user"] *  { color: #f0e8ff !important; background: #2a1f35 !important; }
#chatbot [data-testid="bot"],
#chatbot [data-testid="bot"] *   { color: #d4c8e8 !important; background: #1c1728 !important; }
#chatbot .bubble-wrap             { background: transparent !important; }
#chatbot .prose, #chatbot .prose * { color: inherit !important; }

/* ── Input row ───────────────────────────────────────────────────── */
.input-row {
    background: #16141f;
    border-top: 1px solid #2a2535;
    padding: 14px 16px !important;
    gap: 10px !important;
}
#msg-input textarea {
    background: #0f0e17 !important;
    border: 1px solid #2e2540 !important;
    border-radius: 12px !important;
    color: #e8dff0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 12px 16px !important;
    resize: none !important;
    transition: border-color .2s;
}
#msg-input textarea:focus {
    border-color: #c8956c !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(200,149,108,.12) !important;
}
#msg-input textarea::placeholder { color: #4a3f52 !important; }

#send-btn {
    background: linear-gradient(135deg, #c8956c, #b07650) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.04em;
    padding: 0 22px !important;
    height: 44px !important;
    transition: opacity .18s, transform .18s;
    cursor: pointer;
    min-width: 90px !important;
}
#send-btn:hover { opacity: .88; transform: translateY(-1px); }
#send-btn:active { transform: translateY(0); }

/* ── Meta row (user-id + clear) ──────────────────────────────────── */
.meta-row {
    background: #16141f;
    border-top: 1px solid #1e1b28;
    padding: 10px 16px !important;
    gap: 8px !important;
}
.meta-row label { color: #5a4f62 !important; font-size: 0.75rem !important; }
.meta-row input {
    background: #0f0e17 !important;
    border: 1px solid #2a2535 !important;
    border-radius: 8px !important;
    color: #7a6f82 !important;
    font-size: 0.82rem !important;
}
#clear-btn {
    background: transparent !important;
    border: 1px solid #2a2535 !important;
    border-radius: 8px !important;
    color: #5a4f62 !important;
    font-size: 0.82rem !important;
    transition: border-color .18s, color .18s;
}
#clear-btn:hover { border-color: #8b3a3a !important; color: #c87070 !important; }

/* ── Sidebar panels ──────────────────────────────────────────────── */
.sidebar-panel {
    background: #16141f;
    border: 1px solid #2a2535;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 14px;
}
.panel-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.1rem !important;
    font-weight: 400 !important;
    color: #c8bfd8 !important;
    letter-spacing: 0.05em;
    margin-bottom: 12px !important;
}

/* ── Music card ──────────────────────────────────────────────────── */
.music-card {
    background: #1c1728;
    border: 1px solid #3d2e50;
    border-radius: 14px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.music-track-row {
    display: flex;
    gap: 14px;
    align-items: center;
}
.vinyl-wrap {
    width: 64px; height: 64px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
    border: 3px solid #3d2e50;
    animation: spin-vinyl 12s linear infinite;
    animation-play-state: paused;
}
.vinyl-wrap.playing { animation-play-state: running; }
.vinyl-wrap img {
    width: 100%; height: 100%;
    object-fit: cover;
    border-radius: 50%;
}
@keyframes spin-vinyl { to { transform: rotate(360deg); } }

audio {
    width: 100% !important;
    height: 32px !important;
    border-radius: 8px !important;
    filter: invert(1) hue-rotate(200deg) brightness(.7);
}
.music-link {
    font-size: 0.75rem;
    color: #c8956c;
    text-decoration: none;
    letter-spacing: 0.04em;
}
.music-link:hover { color: #e8b484; }

/* ── Tool log badges ─────────────────────────────────────────────── */
.tool-log-entry {
    border-left: 2px solid #3d2e50;
    padding: 8px 0 8px 12px;
    margin-bottom: 10px;
    animation: slide-in .3s ease;
}
@keyframes slide-in {
    from { opacity:0; transform: translateX(-6px); }
    to   { opacity:1; transform: translateX(0);    }
}
.tool-badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 6px;
}
.badge-emotion  { background: #2a1f3a; color: #c8a0e8; border: 1px solid #4a3060; }
.badge-coping   { background: #1a2a25; color: #7ec8a0; border: 1px solid #2a4a38; }
.badge-music    { background: #2a2015; color: #e8c87a; border: 1px solid #4a3c20; }
.badge-mood     { background: #1a2030; color: #7ab0e8; border: 1px solid #2a3850; }
.badge-other    { background: #252030; color: #a09ab8; border: 1px solid #3a3050; }

/* ── Tool legend ─────────────────────────────────────────────────── */
.tool-legend {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 4px;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: #6b5e6a;
}

/* ── Scrollbar ───────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2535; border-radius: 2px; }

/* ── Gradio overrides ────────────────────────────────────────────── */
.gr-form, .gr-box  { background: transparent !important; border: none !important; }
footer             { display: none !important; }
.gr-button         { font-family: 'DM Sans', sans-serif !important; }
label span         { color: #5a4f62 !important; font-size: 0.75rem !important; }
"""

# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

HEADER_HTML = """
<div class="mindease-header">
  <p class="mindease-title">✦ MindEase</p>
  <p class="mindease-subtitle">your quiet space to breathe, feel, and heal</p>
</div>
<div class="status-bar">
  <span class="status-dot"></span>
  <span>local model · private · always free</span>
</div>
"""

MUSIC_PLACEHOLDER = """
<div style="text-align:center;padding:28px 0;color:#3d2e50;">
  <div style="font-size:2.2rem;margin-bottom:8px;opacity:.5;">♪</div>
  <div style="font-size:0.8rem;color:#4a3f52;letter-spacing:.06em;">
    music matched to your mood<br>will appear here
  </div>
</div>
"""

TOOL_PLACEHOLDER = """
<div style="color:#3d2e50;font-size:0.8rem;letter-spacing:.04em;
            text-align:center;padding:16px 0;">
  waiting for conversation…
</div>
"""

LEGEND_HTML = """
<div class="tool-legend">
  <div class="legend-item"><span class="tool-badge badge-emotion">🧠 emotion</span> analyze_emotion</div>
  <div class="legend-item"><span class="tool-badge badge-coping">💡 coping</span> get_coping_strategy</div>
  <div class="legend-item"><span class="tool-badge badge-music">🎵 music</span> search_music · iTunes API</div>
  <div class="legend-item"><span class="tool-badge badge-mood">📓 journal</span> log_mood · SQLite</div>
</div>
"""

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _build_music_card(tool_log: list) -> str:
    for entry in reversed(tool_log):
        if entry["tool"] != "search_music":
            continue
        r       = entry["result"]
        track   = r.get("track_name", "Unknown")
        artist  = r.get("artist", "Unknown")
        artwork = r.get("artwork_url", "")
        preview = r.get("preview_url", "")
        url     = r.get("track_url", "")
        genre   = r.get("genre", "")
        source  = r.get("source", "")

        artwork_inner = (
            f'<img src="{artwork}" alt="{track}" />'
            if artwork else
            '<div style="width:100%;height:100%;background:#2a1f35;'
            'display:flex;align-items:center;justify-content:center;'
            'font-size:1.6rem;border-radius:50%;">♪</div>'
        )
        import time as _time
        cache_bust = int(_time.time())
        # Store preview URL in a data attribute on the button.
        # On click, JS creates a brand-new Audio() object from scratch —
        # no DOM audio element is ever reused, so there is zero caching.
        preview_html = (
            f'''
<div style="margin-top:10px;">
  <button
    data-src="{preview}"
    data-ts="{cache_bust}"
    onclick="
      var btn=this;
      var src=btn.getAttribute('data-src');
      /* Kill any previously playing audio stored on window */
      if(window._meAudio){{
        window._meAudio.pause();
        window._meAudio.src=\'\';
        window._meAudio=null;
      }}
      /* Create a completely fresh Audio object */
      var a=new Audio(src);
      window._meAudio=a;
      btn.textContent='▶  loading…';
      a.oncanplay=function(){{btn.textContent='▶  play preview';}};
      a.onended=function(){{btn.textContent='▶  play preview';window._meAudio=null;}};
      a.onerror=function(){{btn.textContent='⚠ preview unavailable';}};
      a.play().then(function(){{btn.textContent='⏸  playing';}}).catch(function(){{btn.textContent='▶  play preview';}});
    "
    style="
      width:100%;padding:9px 0;
      background:#2a1f35;border:1px solid #4a3060;border-radius:10px;
      color:#c8a0e8;font-size:0.85rem;letter-spacing:0.04em;
      cursor:pointer;transition:background .18s;
    "
    onmouseover="this.style.background='#3a2f45'"
    onmouseout="this.style.background='#2a1f35'"
  >▶  play preview</button>
</div>
'''
            if preview else ""
        )
        link_html = (
            f'<a class="music-link" href="{url}" target="_blank">'
            f'open in iTunes ↗</a>' if url else ""
        )
        fallback_badge = (
            '<span style="font-size:.65rem;color:#8b7050;margin-left:6px;">'
            '(offline fallback)</span>' if source == "fallback" else ""
        )
        return f"""
<div class="music-card">
  <div class="music-track-row">
    <div class="vinyl-wrap" id="vinyl-art">{artwork_inner}</div>
    <div style="flex:1;min-width:0;">
      <div style="font-family:'Cormorant Garamond',serif;font-size:1.05rem;
                  color:#e8dff0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
        {track}{fallback_badge}
      </div>
      <div style="font-size:.82rem;color:#8b7e88;margin-top:2px;">{artist}</div>
      <div style="font-size:.72rem;color:#4a3f52;margin-top:1px;
                  text-transform:uppercase;letter-spacing:.06em;">{genre}</div>
    </div>
  </div>
  {preview_html}
  {link_html}
</div>
"""
    return MUSIC_PLACEHOLDER


def _build_tool_log(tool_log_state: list) -> str:
    if not tool_log_state:
        return TOOL_PLACEHOLDER

    badge_class = {
        "analyze_emotion":     "badge-emotion",
        "get_coping_strategy": "badge-coping",
        "search_music":        "badge-music",
        "log_mood":            "badge-mood",
    }
    icon_map = {
        "analyze_emotion":     "🧠",
        "get_coping_strategy": "💡",
        "search_music":        "🎵",
        "log_mood":            "📓",
    }
    lines = []
    for entry in reversed(tool_log_state[-8:]):
        name    = entry["tool"]
        icon    = icon_map.get(name, "🔧")
        bcls    = badge_class.get(name, "badge-other")
        # Build a short readable summary of result
        res     = entry["result"]
        if name == "analyze_emotion":
            summary = f"emotion={res.get('emotion','?')}  intensity={res.get('intensity','?')}  conf={res.get('confidence','?')}"
        elif name == "get_coping_strategy":
            summary = res.get("title", "")
        elif name == "search_music":
            summary = f"{res.get('track_name','?')} — {res.get('artist','?')}"
        elif name == "log_mood":
            summary = f"saved entry #{res.get('id','?')}  @ {res.get('timestamp','')[:16]}"
        else:
            summary = str(res)[:80]

        lines.append(f"""
<div class="tool-log-entry">
  <span class="tool-badge {bcls}">{icon} {name}</span>
  <div style="font-size:.76rem;color:#5a4f6a;margin-top:4px;
              font-family:'DM Mono',monospace;">{summary}</div>
</div>""")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def chat(message, chat_history, agent_history, user_id, tool_log_state):
    if not message.strip():
        return "", chat_history, agent_history, tool_log_state, TOOL_PLACEHOLDER, MUSIC_PLACEHOLDER

    try:
        reply, new_agent_history, tool_log = run_agent(
            user_message=message,
            history=agent_history,
            user_id=user_id or "anonymous",
        )
    except RuntimeError as exc:
        err_reply = f"⚠️  {exc}"
        chat_history = chat_history + [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": err_reply},
        ]
        return "", chat_history, agent_history, tool_log_state, \
               _build_tool_log(tool_log_state), _build_music_card(tool_log_state)

    chat_history   = chat_history + [
        {"role": "user",      "content": message},
        {"role": "assistant", "content": reply},
    ]
    tool_log_state = tool_log_state + tool_log

    return (
        "",
        chat_history,
        new_agent_history,
        tool_log_state,
        _build_tool_log(tool_log_state),
        _build_music_card(tool_log_state),
    )


def clear_chat():
    return [], [], [], TOOL_PLACEHOLDER, MUSIC_PLACEHOLDER, ""


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

with gr.Blocks(title="MindEase", head="""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
""") as demo:

    agent_history  = gr.State([])
    tool_log_state = gr.State([])

    # Header
    gr.HTML(HEADER_HTML)

    with gr.Row(equal_height=True):

        # ── Left: chat ────────────────────────────────────────────────────────
        with gr.Column(scale=5, elem_id="chat-col"):
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                label="",
                show_label=False,
                placeholder="<div style='text-align:center;color:#3d2e50;padding:60px 0;'>"
                            "<div style='font-size:2rem;margin-bottom:12px;'>✦</div>"
                            "<div style='font-family:Cormorant Garamond,serif;font-size:1.1rem;"
                            "color:#4a3f52;'>Share what's on your mind…</div></div>",
            )

            with gr.Row(elem_classes="input-row"):
                msg_input = gr.Textbox(
                    placeholder="How are you feeling right now?",
                    show_label=False,
                    lines=1,
                    max_lines=3,
                    scale=6,
                    container=False,
                    elem_id="msg-input",
                )
                send_btn = gr.Button("send", scale=1, elem_id="send-btn")

            with gr.Row(elem_classes="meta-row"):
                user_id_box = gr.Textbox(
                    value="user_001",
                    label="session id",
                    scale=3,
                    container=True,
                )
                clear_btn = gr.Button("✕ clear", scale=1, elem_id="clear-btn")

        # ── Right: sidebar ────────────────────────────────────────────────────
        with gr.Column(scale=2):

            # Music panel
            with gr.Group(elem_classes="sidebar-panel"):
                gr.HTML('<p class="panel-title">♪ now playing</p>')
                music_display = gr.HTML(value=MUSIC_PLACEHOLDER)

            # Tool log panel
            with gr.Group(elem_classes="sidebar-panel"):
                gr.HTML('<p class="panel-title">⟳ agent activity</p>')
                tool_display = gr.HTML(value=TOOL_PLACEHOLDER)

            # Legend panel
            with gr.Group(elem_classes="sidebar-panel"):
                gr.HTML('<p class="panel-title" style="margin-bottom:8px;">tools</p>')
                gr.HTML(LEGEND_HTML)

    # ── Events ────────────────────────────────────────────────────────────────
    _inputs  = [msg_input, chatbot, agent_history, user_id_box, tool_log_state]
    _outputs = [msg_input, chatbot, agent_history, tool_log_state, tool_display, music_display]

    send_btn.click(fn=chat, inputs=_inputs, outputs=_outputs)
    msg_input.submit(fn=chat, inputs=_inputs, outputs=_outputs)
    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot, agent_history, tool_log_state,
                 tool_display, music_display, msg_input],
    )


if __name__ == "__main__":
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7861,   # different port so you can run both app.py and app2.py
        css=CSS,
    )
