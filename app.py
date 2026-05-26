import streamlit as st
import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import html


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

# =========================================================
# OPENROUTER API KEY & MODEL
# =========================================================

load_dotenv()
API_KEY   = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "openrouter/free"

# =========================================================
# HELPERS — render a single message bubble
# =========================================================

def safe_html(text):
    """Escape raw text so HTML tags/symbols never break the bubble layout."""
    return html.escape(str(text)).replace("\n", "<br>")

def render_user_bubble(content, time_str, animate=False):
    cls = "message-row user new-msg" if animate else "message-row user"
    st.markdown(f"""
    <div class="{cls}">
        <div class="user-message">
            {safe_html(content)}
            <div class="msg-timestamp">{time_str}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def render_bot_bubble(content, time_str, animate=False):
    cls = "message-row bot new-msg" if animate else "message-row bot"
    st.markdown(f"""
    <div class="{cls}">
        <div class="bot-avatar">✦</div>
        <div class="bot-message">
            {safe_html(content)}
            <div class="msg-timestamp">{time_str}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def render_typing():
    st.markdown("""
    <div class="message-row bot" id="typing-indicator">
        <div class="bot-avatar">✦</div>
        <div class="bot-message typing-wrap">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary:    #050510;
    --glass-border:  rgba(255,255,255,0.12);
    --user-bubble:   rgba(99,102,241,0.85);
    --user-glow:     rgba(99,102,241,0.4);
    --bot-bubble:    rgba(255,255,255,0.07);
    --bot-border:    rgba(255,255,255,0.13);
    --accent:        #818cf8;
    --accent2:       #a78bfa;
    --text-primary:  rgba(255,255,255,0.95);
    --text-secondary:rgba(255,255,255,0.55);
    --font:         'Plus Jakarta Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--font) !important;
    color: var(--text-primary);
}

/* ── Background ─────────────────────────────────────── */
.stApp {
    background: var(--bg-primary) !important;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 20% 10%, rgba(99,102,241,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 80%, rgba(167,139,250,0.14) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 50% 40%, rgba(56,189,248,0.07) 0%, transparent 60%);
    pointer-events: none; z-index: 0;
    animation: meshShift 12s ease-in-out infinite alternate;
}
.stApp::after {
    content: '';
    position: fixed; top: -120px; right: -120px;
    width: 420px; height: 420px; border-radius: 50%;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
    animation: orbFloat 8s ease-in-out infinite;
}
@keyframes meshShift {
    0%   { opacity:1;   transform:scale(1) translateY(0); }
    50%  { opacity:0.8; transform:scale(1.03) translateY(-8px); }
    100% { opacity:1;   transform:scale(1) translateY(0); }
}
@keyframes orbFloat {
    0%,100% { transform:translate(0,0) scale(1); }
    50%      { transform:translate(-30px,30px) scale(1.08); }
}

/* ── Layout ──────────────────────────────────────────── */
.main .block-container {
    max-width: 680px !important;
    padding: 2rem 1.2rem 6rem !important;
    position: relative; z-index: 1;
}

/* ── Title ───────────────────────────────────────────── */
.main-title {
    text-align: center; font-size: 30px; font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg,#fff 30%,var(--accent) 70%,var(--accent2) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0 0 6px 0; padding-top: 4px;
    animation: titleReveal 0.8s cubic-bezier(0.16,1,0.3,1) both;
}
.main-subtitle {
    text-align: center; font-size: 13px; font-weight: 400;
    color: var(--text-secondary); margin-bottom: 28px; letter-spacing: 0.3px;
    animation: titleReveal 0.9s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes titleReveal {
    from { opacity:0; transform:translateY(-16px); }
    to   { opacity:1; transform:translateY(0); }
}

/* ── Status pill ─────────────────────────────────────── */
.status-pill {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: 50px; padding: 4px 12px;
    font-size: 11.5px; font-weight: 500; color: #4ade80;
    margin: 0 auto 24px; display: block; width: fit-content;
    backdrop-filter: blur(8px);
    animation: pillPop 0.6s cubic-bezier(0.34,1.56,0.64,1) 0.3s both;
}
.status-dot {
    width: 6px; height: 6px; background: #4ade80;
    border-radius: 50%; display: inline-block;
    animation: pulseDot 2s ease-in-out infinite;
}
@keyframes pulseDot {
    0%,100% { box-shadow: 0 0 0 0 rgba(74,222,128,0.6); }
    50%      { box-shadow: 0 0 0 5px rgba(74,222,128,0); }
}
@keyframes pillPop {
    from { opacity:0; transform:scale(0.8); }
    to   { opacity:1; transform:scale(1); }
}

/* ── Message rows ────────────────────────────────────── */
.message-row {
    display: flex;
    margin: 10px 0;
}

/* Standard history messages — no animation (instant) */
.message-row:not(.new-msg) {
    opacity: 1;
    transform: none;
}

/* NEW message — fly-in from bottom */
.message-row.new-msg {
    animation: flyIn 0.42s cubic-bezier(0.16,1,0.3,1) both;
}

@keyframes flyIn {
    0%   { opacity:0; transform:translateY(28px) scale(0.95); }
    60%  { opacity:1; transform:translateY(-4px) scale(1.01); }
    100% { opacity:1; transform:translateY(0)   scale(1); }
}

/* User bubble */
.message-row.user { justify-content: flex-end; }
.user-message {
    background: var(--user-bubble);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(129,140,248,0.35);
    box-shadow: 0 4px 24px var(--user-glow), inset 0 1px 0 rgba(255,255,255,0.18);
    color: #fff; padding: 12px 16px;
    border-radius: 22px 22px 6px 22px;
    max-width: 75%; font-size: 15px; font-weight: 400;
    line-height: 1.5; word-break: break-word;
}

/* Bot bubble */
.message-row.bot { justify-content: flex-start; align-items: flex-end; gap: 10px; }
.bot-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: linear-gradient(135deg,var(--accent) 0%,var(--accent2) 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
    box-shadow: 0 2px 12px rgba(99,102,241,0.4);
}
.bot-message {
    background: var(--bot-bubble);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid var(--bot-border);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.92); padding: 12px 16px;
    border-radius: 22px 22px 22px 6px;
    max-width: 75%; font-size: 15px; font-weight: 400;
    line-height: 1.6; word-break: break-word;
}

/* Typing dots */
.typing-wrap { min-width: 56px; }
.typing-dots { display:inline-flex; gap:5px; align-items:center; padding:4px 2px; }
.typing-dots span {
    width:8px; height:8px; background:rgba(255,255,255,0.45);
    border-radius:50%; display:inline-block;
    animation: dotBounce 1.3s ease-in-out infinite;
}
.typing-dots span:nth-child(1) { animation-delay:0s; }
.typing-dots span:nth-child(2) { animation-delay:0.18s; }
.typing-dots span:nth-child(3) { animation-delay:0.36s; }
@keyframes dotBounce {
    0%,80%,100% { transform:translateY(0)   scale(0.75); opacity:0.4; }
    40%          { transform:translateY(-7px) scale(1.1);  opacity:1; }
}

/* Timestamp */
.msg-timestamp {
    font-size: 10px; color: rgba(255,255,255,0.4);
    margin-top: 5px; font-weight: 400; letter-spacing: 0.2px;
}

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(8,8,20,0.85) !important;
    backdrop-filter: blur(30px) saturate(150%) !important;
    -webkit-backdrop-filter: blur(30px) saturate(150%) !important;
    border-right: 1px solid var(--glass-border) !important;
}
[data-testid="stSidebar"] .block-container { padding: 2rem 1.2rem !important; }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: var(--font) !important; font-weight: 600 !important;
    font-size: 16px !important; color: var(--text-primary) !important;
}
[data-testid="stSidebar"] code {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 10px !important; color: var(--accent) !important;
    font-size: 11px !important; padding: 8px 10px !important;
    display: block !important; word-break: break-all;
}
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(34,197,94,0.1) !important;
    border: 1px solid rgba(34,197,94,0.22) !important;
    border-radius: 14px !important; color: #4ade80 !important;
    font-size: 13px !important; backdrop-filter: blur(10px) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: var(--text-secondary) !important;
    font-family: var(--font) !important; font-size: 13px !important;
}
[data-testid="stSidebar"] button {
    background: rgba(239,68,68,0.1) !important;
    border: 1px solid rgba(239,68,68,0.25) !important;
    border-radius: 14px !important; color: #f87171 !important;
    font-family: var(--font) !important; font-size: 13px !important;
    font-weight: 500 !important; padding: 10px 18px !important;
    width: 100% !important; backdrop-filter: blur(10px) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] button:hover {
    background: rgba(239,68,68,0.2) !important;
    border-color: rgba(239,68,68,0.45) !important;
    box-shadow: 0 0 18px rgba(239,68,68,0.2) !important;
    transform: translateY(-1px) !important;
}

/* ── Chat Input ──────────────────────────────────────── */
[data-testid="stChatInput"] {
    position: fixed !important; bottom: 0 !important;
    left: 50% !important; transform: translateX(-50%) !important;
    width: min(680px,100vw) !important; padding: 12px 16px !important;
    background: rgba(5,5,16,0.75) !important;
    backdrop-filter: blur(30px) saturate(200%) !important;
    -webkit-backdrop-filter: blur(30px) saturate(200%) !important;
    border-top: 1px solid var(--glass-border) !important; z-index: 999 !important;
}
[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 22px !important; backdrop-filter: blur(10px) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.25) !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: rgba(129,140,248,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12), 0 4px 24px rgba(0,0,0,0.3) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important; color: var(--text-primary) !important;
    font-family: var(--font) !important; font-size: 15px !important;
    caret-color: var(--accent) !important;
    padding: 12px 16px !important; border: none !important; outline: none !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: rgba(255,255,255,0.3) !important; }
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg,var(--accent),var(--accent2)) !important;
    border: none !important; border-radius: 50% !important;
    width: 36px !important; height: 36px !important; margin: 4px !important;
    transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important;
    box-shadow: 0 2px 12px rgba(99,102,241,0.4) !important;
}
[data-testid="stChatInput"] button:hover {
    transform: scale(1.1) !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.6) !important;
}

/* ── Empty state ─────────────────────────────────────── */
.empty-state { text-align:center; padding:60px 20px; animation:titleReveal 0.8s ease both; }
.empty-icon {
    font-size:52px; margin-bottom:16px; display:block;
    filter:drop-shadow(0 0 24px rgba(99,102,241,0.5));
    animation:iconFloat 4s ease-in-out infinite;
}
@keyframes iconFloat {
    0%,100% { transform:translateY(0); }
    50%      { transform:translateY(-8px); }
}
.empty-title { font-size:20px; font-weight:600; color:rgba(255,255,255,0.8); margin-bottom:8px; }
.empty-sub   { font-size:14px; color:var(--text-secondary); line-height:1.6; }

/* ── Footer / misc ───────────────────────────────────── */
.footer {
    text-align:center; color:rgba(255,255,255,0.25);
    font-size:11.5px; font-weight:400; margin-top:20px;
}
hr { border:none !important; border-top:1px solid var(--glass-border) !important; margin:16px 0 !important; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:rgba(255,255,255,0.2); }

#MainMenu, footer, header { visibility:hidden !important; }
[data-testid="stDecoration"] { display:none !important; }

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================================================
# TITLE
# =========================================================

st.markdown('<div class="main-title">🐐 Goat AI</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Powered by ZEROTRACE · Always free</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="status-pill"><span class="status-dot"></span> Connected &amp; Ready</div>',
    unsafe_allow_html=True
)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.success("✅ Free AI Connected")
    st.markdown("**Model**")
    st.code(MODEL_NAME)
    st.markdown("---")
    msg_count = len(st.session_state.messages)
    st.markdown(
        f"<p style='color:rgba(255,255,255,0.4);font-size:12px;'>"
        f"💬 {msg_count} message{'s' if msg_count!=1 else ''} in history</p>",
        unsafe_allow_html=True
    )
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# =========================================================
# CHAT INPUT (placed early so Streamlit captures it)
# =========================================================

prompt = st.chat_input("Message AI Assistant…")

# =========================================================
# RENDER HISTORY  (no animation — already seen)
# =========================================================

if not st.session_state.messages and not prompt:
    st.markdown("""
    <div class="empty-state">
        <span class="empty-icon">🤖</span>
        <div class="empty-title">How can I help you today?</div>
        <div class="empty-sub">Ask me anything — I'm here to assist.</div>
    </div>""", unsafe_allow_html=True)

for message in st.session_state.messages:
    if message["role"] == "user":
        render_user_bubble(message["content"], message["time"], animate=False)
    else:
        render_bot_bubble(message["content"], message["time"], animate=False)

# =========================================================
# HANDLE NEW PROMPT — render IMMEDIATELY, then call API
# =========================================================

if prompt:
    current_time = datetime.now().strftime("%H:%M")

    # 1️⃣  Show user bubble RIGHT NOW with fly-in animation
    render_user_bubble(prompt, current_time, animate=True)

    # 2️⃣  Show animated typing indicator while waiting
    typing_slot = st.empty()
    with typing_slot:
        render_typing()

    # 3️⃣  Call the API (happens while typing indicator is visible)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Streamlit AI Chatbot"
    }

    # Include full history + new user message
    messages_for_api = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ] + [{"role": "user", "content": prompt}]

    data = {
        "model": MODEL_NAME,
        "messages": messages_for_api,
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        result = response.json()
        if "choices" in result:
            ai_reply = result["choices"][0]["message"]["content"]
        elif "error" in result:
            ai_reply = f"❌ API Error: {result['error']['message']}"
        else:
            ai_reply = "❌ Unexpected API Response"
    except Exception as e:
        ai_reply = f"❌ Error: {str(e)}"

    # 4️⃣  Replace typing indicator with actual bot reply (fly-in)
    typing_slot.empty()
    render_bot_bubble(ai_reply, current_time, animate=True)

    # 5️⃣  Persist both messages to session state
    st.session_state.messages.append({"role": "user",      "content": prompt,   "time": current_time})
    st.session_state.messages.append({"role": "assistant", "content": ai_reply, "time": current_time})

# =========================================================
# FOOTER
# =========================================================

st.markdown('<div class="footer">Built with Streamlit + OpenRouter 🚀</div>', unsafe_allow_html=True)
