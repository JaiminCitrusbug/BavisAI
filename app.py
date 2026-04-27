import html as html_lib

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

st.set_page_config(
    page_title="Bavis Support Assistant",
    page_icon="https://bavis.com/wp-content/uploads/2024/04/bavis-horizontal-red.svg",
    layout="wide",
)
load_dotenv()

st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">

<style>
html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.main {
    background: #efefef !important;
    font-family: "DM Sans", sans-serif;
    height: 100%;
    overflow: hidden !important;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
    min-height: 100vh;
    overflow: hidden !important;
}

.block-container > div {
    width: 100%;
}

footer,
#MainMenu,
[data-testid="stHeader"],
.stDeployButton {
    display: none !important;
}

.stMarkdown,
.element-container {
    margin: 0 !important;
    padding: 0 !important;
}

.element-container:has([data-testid="stIFrame"]) {
    flex: 1 1 auto;
    min-height: 0;
}

[data-testid="stForm"] {
    display: none !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    pointer-events: none !important;
}

.bv-header {
    background: #ffffff;
    border-bottom: 3px solid #c8102e;
    padding: 0.85rem 2rem;
    display: flex;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 999;
    box-shadow: 0 2px 14px rgba(0, 0, 0, 0.07);
}

.bv-header img {
    height: 28px;
    display: block;
}

.bv-header-sub {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #c0c0c0;
    margin-left: 0.85rem;
    padding-left: 0.85rem;
    border-left: 1.5px solid #ebebeb;
    line-height: 1;
}

.bv-hero {
    background: #141414;
    background-image:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(200, 16, 46, 0.22) 0%, transparent 60%),
        linear-gradient(180deg, #1c1c1c 0%, #111111 100%);
    padding: 1.3rem 2rem 1.15rem;
    text-align: center;
    position: relative;
}

.bv-hero::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 5%, #c8102e 40%, #c8102e 60%, transparent 95%);
    opacity: 0.6;
}

.bv-hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(200, 16, 46, 0.15);
    border: 1px solid rgba(200, 16, 46, 0.4);
    color: #ff6b85;
    font-size: 0.61rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    padding: 0.28rem 0.85rem;
    border-radius: 100px;
    margin-bottom: 0.65rem;
}

.bv-hero-badge::before {
    content: "";
    width: 6px;
    height: 6px;
    background: #ff6b85;
    border-radius: 50%;
    animation: heroPulse 2s ease-in-out infinite;
}

@keyframes heroPulse {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
    }
    50% {
        opacity: 0.4;
        transform: scale(0.7);
    }
}

.bv-hero h1 {
    font-family: "DM Serif Display", serif;
    color: #ffffff;
    font-size: 1.85rem;
    margin: 0;
    line-height: 1.2;
}

.bv-hero h1 em {
    font-style: italic;
    color: #ff8096;
}

[data-testid="stIFrame"] {
    border: none !important;
    display: block;
    max-width: 1160px;
    width: 100% !important;
    margin: 0.9rem auto 0 !important;
    padding: 0 1rem 1rem;
    box-sizing: border-box;
}

[data-testid="stIFrame"] iframe {
    width: 100% !important;
    height: 100% !important;
    border: none !important;
}

@media (max-width: 768px) {
    .bv-header {
        padding: 0.75rem 1rem;
    }

    .bv-header img {
        height: 24px;
    }

    .bv-header-sub {
        display: none;
    }

    .bv-hero {
        padding: 1rem 1rem 0.95rem;
    }

    .bv-hero h1 {
        font-size: 1.45rem;
    }

    [data-testid="stIFrame"] {
        padding: 0 0.5rem 0.5rem;
        margin-top: 0.65rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="bv-header">
    <img src="https://bavis.com/wp-content/uploads/2024/04/bavis-horizontal-red.svg" alt="Bavis Fabacraft"/>
    <span class="bv-header-sub">Support Assistant</span>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="bv-hero">
    <div class="bv-hero-badge">AI-Powered Support</div>
    <h1>Your <em>Bavis Support</em> Assistant</h1>
</div>
""",
    unsafe_allow_html=True,
)

if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "loading" not in st.session_state:
    st.session_state.loading = False

GREETING = (
    "Hello! I'm your Bavis Fabacraft Support Assistant. "
    "I can help with installation steps, assembly and setup guidance, "
    "product specifications, troubleshooting, and manual lookups.\n\n"
    "What can I help you with today?"
)

if not st.session_state.initialized:
    st.session_state.msgs.append({"role": "assistant", "content": GREETING})
    st.session_state.initialized = True


def build_chat_html(messages, is_loading):
    bubbles = ""
    for message in messages:
        role = message["role"]
        safe = html_lib.escape(message["content"]).replace("\n", "<br>")
        if role == "user":
            bubbles += f"""
            <div class="row user">
              <div class="bubble user">
                <div class="lbl">You</div>
                {safe}
              </div>
            </div>"""
        else:
            bubbles += f"""
            <div class="row bot">
              <div class="av-sm">BF</div>
              <div class="bubble bot">
                <div class="lbl">Bavis Assistant</div>
                {safe}
              </div>
            </div>"""

    if is_loading:
        bubbles += """
        <div class="row bot">
          <div class="av-sm">BF</div>
          <div class="bubble bot">
            <div class="lbl">Bavis Assistant</div>
            <div class="typing"><span></span><span></span><span></span></div>
          </div>
        </div>"""

    disabled_attr = "disabled" if is_loading else ""
    autofocus_js = (
        ""
        if is_loading
        else "setTimeout(function(){document.getElementById('user-input').focus();},120);"
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

html,
body {{
    font-family: "DM Sans", sans-serif;
    background: transparent;
    height: 100%;
    overflow: hidden;
}}

body {{
    display: flex;
    flex-direction: column;
    height: 100%;
}}

.card {{
    width: 100%;
    height: 100%;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 16px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 8px 48px rgba(0, 0, 0, 0.11);
}}

.status {{
    background: linear-gradient(135deg, #c8102e 0%, #9e0b23 100%);
    padding: 0.88rem 1.4rem;
    display: flex;
    align-items: center;
    gap: 0.85rem;
    flex-shrink: 0;
    box-shadow: 0 2px 10px rgba(200, 16, 46, 0.22);
}}

.av {{
    width: 42px;
    height: 42px;
    background: rgba(255, 255, 255, 0.15);
    border: 2px solid rgba(255, 255, 255, 0.4);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 800;
    color: #ffffff;
    flex-shrink: 0;
    letter-spacing: -0.02em;
}}

.status-info {{
    flex: 1;
    min-width: 0;
}}

.status-name {{
    font-size: 0.92rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.01em;
}}

.status-sub {{
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.76);
    margin-top: 3px;
    display: flex;
    align-items: center;
    gap: 7px;
}}

.dot {{
    width: 7px;
    height: 7px;
    background: #4ade80;
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 0 0 2px rgba(74, 222, 128, 0.3);
    animation: blink 2.5s ease-in-out infinite;
}}

@keyframes blink {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.45; }}
}}

.status-badge {{
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.25);
    color: rgba(255, 255, 255, 0.85);
    font-size: 0.58rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.2rem 0.65rem;
    border-radius: 100px;
    flex-shrink: 0;
}}

.messages {{
    flex: 1;
    min-height: 0;
    padding: 1.3rem 1.3rem 0.8rem;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    overflow-y: auto;
    overflow-x: hidden;
    background: #f7f7f7;
    scroll-behavior: smooth;
}}

.messages::-webkit-scrollbar {{
    width: 4px;
}}

.messages::-webkit-scrollbar-thumb {{
    background: #d6d6d6;
    border-radius: 10px;
}}

.sep {{
    text-align: center;
    font-size: 0.59rem;
    color: #c8c8c8;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
}}

.sep::before,
.sep::after {{
    content: "";
    flex: 1;
    height: 1px;
    background: #e6e6e6;
}}

.row {{
    display: flex;
    gap: 0.55rem;
    align-items: flex-end;
    width: 100%;
}}

.row.bot {{
    flex-direction: row;
}}

.row.user {{
    flex-direction: row-reverse;
}}

.av-sm {{
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #c8102e 0%, #9e0b23 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.54rem;
    font-weight: 800;
    color: #ffffff;
    flex-shrink: 0;
    margin-bottom: 2px;
    box-shadow: 0 2px 8px rgba(200, 16, 46, 0.28);
}}

.bubble {{
    max-width: 73%;
    padding: 0.8rem 1rem;
    font-size: 0.875rem;
    line-height: 1.72;
    word-break: break-word;
}}

.bubble.bot {{
    background: #ffffff;
    color: #1a1a1a;
    border: 1px solid #ebebeb;
    border-radius: 3px 14px 14px 14px;
    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.055);
}}

.bubble.user {{
    background: linear-gradient(135deg, #1a2b5a 0%, #0f1c3f 100%);
    color: #ffffff;
    border-radius: 14px 14px 2px 14px;
    box-shadow: 0 3px 12px rgba(26, 43, 90, 0.22);
}}

.lbl {{
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
    color: #c8102e;
}}

.bubble.user .lbl {{
    color: rgba(255, 255, 255, 0.4);
}}

.typing {{
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 2px 0;
    height: 20px;
}}

.typing span {{
    width: 7px;
    height: 7px;
    background: #c8102e;
    border-radius: 50%;
    opacity: 0.4;
    animation: bounce 1.4s infinite ease-in-out both;
}}

.typing span:nth-child(2) {{
    animation-delay: .18s;
}}

.typing span:nth-child(3) {{
    animation-delay: .36s;
}}

@keyframes bounce {{
    0%, 80%, 100% {{
        transform: translateY(0);
        opacity: .35;
    }}
    40% {{
        transform: translateY(-6px);
        opacity: 1;
    }}
}}

.input-area {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.8rem 1rem;
    background: #ffffff;
    border-top: 1px solid #ebebeb;
    flex-shrink: 0;
}}

#user-input {{
    flex: 1;
    min-width: 0;
    border: 1.5px solid #e2e2e2;
    border-radius: 10px;
    padding: 0.65rem 1rem;
    font-family: "DM Sans", sans-serif;
    font-size: 0.875rem;
    color: #1a1a1a;
    background: #f8f8f8;
    outline: none;
    transition: border-color .15s, background .15s, box-shadow .15s;
}}

#user-input:focus {{
    border-color: #c8102e;
    background: #ffffff;
    box-shadow: 0 0 0 3px rgba(200, 16, 46, 0.09);
}}

#user-input::placeholder {{
    color: #adadad;
}}

#user-input:disabled {{
    opacity: .55;
    cursor: not-allowed;
    background: #f2f2f2;
}}

#send-btn {{
    background: linear-gradient(135deg, #c8102e 0%, #9e0b23 100%);
    border: none;
    border-radius: 10px;
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: transform .12s, box-shadow .15s, opacity .15s;
    box-shadow: 0 3px 10px rgba(200, 16, 46, 0.32);
}}

#send-btn:hover:not([disabled]) {{
    transform: scale(1.07);
    box-shadow: 0 5px 16px rgba(200, 16, 46, 0.42);
}}

#send-btn:active:not([disabled]) {{
    transform: scale(0.95);
}}

#send-btn[disabled] {{
    opacity: .4;
    cursor: not-allowed;
}}

#send-btn svg {{
    fill: #ffffff;
    width: 18px;
    height: 18px;
    pointer-events: none;
}}

@media (max-width: 720px) {{
    .status {{
        padding: 0.8rem 1rem;
        gap: 0.7rem;
    }}

    .status-badge {{
        display: none;
    }}

    .messages {{
        padding: 1rem 0.9rem 0.75rem;
    }}

    .bubble {{
        max-width: 88%;
        font-size: 0.82rem;
    }}

    .input-area {{
        padding: 0.75rem;
    }}
}}
</style>
</head>
<body>
<div class="card">
  <div class="status">
    <div class="av">BF</div>
    <div class="status-info">
      <div class="status-name">Bavis Support Assistant</div>
      <div class="status-sub"><span class="dot"></span>Online | Installation, Service &amp; Manuals</div>
    </div>
    <div class="status-badge">AI Powered</div>
  </div>

  <div class="messages" id="scroll">
    <div class="sep">Today</div>
    {bubbles}
  </div>

  <div class="input-area">
    <input id="user-input" type="text"
      placeholder="Ask about assembly, installation, troubleshooting, or manuals..."
      autocomplete="off" {disabled_attr}/>
    <button id="send-btn" {disabled_attr} title="Send">
      <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
    </button>
  </div>
</div>

<script>
function syncFrameSize() {{
    try {{
        if (!window.frameElement || !window.parent) return;
        var frame = window.frameElement;
        var rect = frame.getBoundingClientRect();
        var availableHeight = Math.max(360, window.parent.innerHeight - rect.top - 12);
        frame.style.height = availableHeight + "px";
        frame.style.maxHeight = availableHeight + "px";
        frame.style.width = "100%";
        if (frame.parentElement) {{
            frame.parentElement.style.height = availableHeight + "px";
            frame.parentElement.style.maxHeight = availableHeight + "px";
            frame.parentElement.style.width = "100%";
        }}
    }} catch (e) {{
        console.warn("Resize sync error:", e);
    }}
}}

(function() {{
    var scrollEl = document.getElementById("scroll");
    if (scrollEl) {{
        scrollEl.scrollTop = scrollEl.scrollHeight;
    }}
}})();

syncFrameSize();

function submitToStreamlit(text) {{
    text = (text || "").trim();
    if (!text) return false;
    try {{
        var parentDoc = window.parent.document;
        var input = parentDoc.querySelector('input[aria-label="BAVIS_BRIDGE"]');

        if (!input) {{
            var allInputs = parentDoc.querySelectorAll('input[type="text"]');
            for (var i = 0; i < allInputs.length; i++) {{
                if (allInputs[i].placeholder === "BAVIS_BRIDGE_PLACEHOLDER") {{
                    input = allInputs[i];
                    break;
                }}
            }}
        }}

        if (!input) return false;

        var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
        setter.call(input, text);
        input.dispatchEvent(new window.parent.Event("input", {{ bubbles: true }}));
        input.dispatchEvent(new window.parent.Event("change", {{ bubbles: true }}));

        setTimeout(function() {{
            var buttons = parentDoc.querySelectorAll("button");
            for (var j = 0; j < buttons.length; j++) {{
                if ((buttons[j].innerText || "").trim() === "BAVIS_SUBMIT") {{
                    buttons[j].click();
                    return;
                }}
            }}
            var fallback = parentDoc.querySelector('[data-testid="stFormSubmitButton"]');
            if (fallback) {{
                fallback.click();
            }}
        }}, 30);

        return true;
    }} catch (e) {{
        console.warn("Bridge error:", e);
        return false;
    }}
}}

var inputEl = document.getElementById("user-input");
var sendBtn = document.getElementById("send-btn");

function handleSend() {{
    var text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = "";
    inputEl.disabled = true;
    sendBtn.disabled = true;
    submitToStreamlit(text);
}}

sendBtn.addEventListener("click", handleSend);
inputEl.addEventListener("keydown", function(e) {{
    if (e.key === "Enter" && !e.shiftKey) {{
        e.preventDefault();
        handleSend();
    }}
}});

window.addEventListener("load", syncFrameSize);
window.addEventListener("resize", syncFrameSize);
if (window.parent) {{
    window.parent.addEventListener("resize", syncFrameSize);
}}
setTimeout(syncFrameSize, 0);
setTimeout(syncFrameSize, 150);
setTimeout(syncFrameSize, 400);

{autofocus_js}
</script>
</body>
</html>"""


components.html(
    build_chat_html(st.session_state.msgs, st.session_state.loading),
    height=800,
    scrolling=False,
)

with st.form("bavis_bridge_form", clear_on_submit=True):
    bridge_msg = st.text_input(
        "BAVIS_BRIDGE",
        key="bridge_input",
        label_visibility="collapsed",
        placeholder="BAVIS_BRIDGE_PLACEHOLDER",
    )
    submitted = st.form_submit_button("BAVIS_SUBMIT")

if submitted and bridge_msg and bridge_msg.strip():
    if not st.session_state.loading:
        st.session_state.msgs.append({"role": "user", "content": bridge_msg.strip()})
        st.session_state.loading = True
        st.rerun()

if st.session_state.loading:
    try:
        from pdf_rag_chat import generate_answer

        last_user = st.session_state.msgs[-1]["content"]
        ai_reply = generate_answer(last_user, st.session_state.msgs[:-1])
    except ImportError:
        ai_reply = (
            "The RAG module (pdf_rag_chat.py) could not be found. "
            "Please ensure pdf_rag_chat.py and pdf_retriever.py are in the same directory as this app."
        )
    except Exception as exc:
        ai_reply = f"An error occurred: {exc}"

    st.session_state.msgs.append({"role": "assistant", "content": ai_reply})
    st.session_state.loading = False
    st.rerun()
