import streamlit as st
import openai
import os
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ==========================================================
# SYSTEM PROMPT — Drive-Thru Advisor (Generalized)
# MINIMAL CHANGE: strengthened rules to forbid ANY questions beyond Q1..Q5
# ==========================================================
SYSTEM_PROMPT = """
Act like a professional Drive-Thru Lane Advisor chatbot for drive-thru setups of any type (food, pharmacy, retail, bank, or logistics).

GOAL:
Guide the user through exactly five questions to identify the correct drive-thru delivery system, using deterministic filtering based on a static catalog. 

RESPONSE RULES:
1. Ask only the following five numbered questions (Q1–Q5) in strict order. Never add or invent new questions or topics.  
2. If the user’s answer is unclear or incomplete, ask one concise clarifying question  
3. Once an answer is clear, move directly to the next question without repeating or confirming previous ones.  
4. Keep full context across turns, ensuring each question depends on previous answers.  
5. When all five inputs are collected and clear, output a structured recommendation section — not delimited with “===” or other symbols, and without asterisks, markdown, or emojis.  
6. The recommendation must include:  
   - Recommended system(s) (1–2 options)  
   - Short rationale explaining the choice and trade-offs  
   - Datasheet and BIM links  
   - A “Site-Check Checklist” with 3–5 validation steps
7. Never ask questions after the recommendation.

QUESTIONS (in this exact order):
Q1 — What items will be delivered (e.g., cash, food, prescriptions, documents, etc.)?  
Q2 — What is the distance or layout requirement (e.g., straight/angled, number of lanes, sender-receiver distance)?  
Q3 — What are the size or space constraints (width, height, available installation space)?  
Q4 — What is the maintenance or downtime tolerance (low-maintenance, high-speed, etc.)?  
Q5 — What is the approximate budget or range?  

RECOMMENDATION LOGIC:
After Q5, use the static catalog below to filter and rank the most suitable options based on matching criteria (item type, distance, maintenance, and budget).  
Do not fabricate or modify catalog data. If multiple systems fit, list both with clear differentiation.

STATIC CATALOG (use as-is):
[
  {
    "name": "TransTrax Teller System",
    "type": "pneumatic",
    "range": "short to medium (up to 120 ft)",
    "features": ["high reliability", "dual-lane support", "standard-size carrier"],
    "maintenance": "low",
    "budget": "medium",
    "datasheet": "https://example.com/transtrax.pdf",
    "bim": "https://example.com/transtrax.bim"
  },
  {
    "name": "Captive Carrier Track System",
    "type": "mechanical",
    "range": "medium to long (up to 250 ft)",
    "features": ["custom routing", "multi-curve layout", "large items supported"],
    "maintenance": "medium",
    "budget": "high",
    "datasheet": "https://example.com/captivecarrier.pdf",
    "bim": "https://example.com/captivecarrier.bim"
  },
  {
    "name": "TransTrax Compact Tube System",
    "type": "pneumatic",
    "range": "short (up to 60 ft)",
    "features": ["single lane", "compact size", "budget-friendly"],
    "maintenance": "low",
    "budget": "low",
    "datasheet": "https://example.com/transtraxcompact.pdf",
    "bim": "https://example.com/transtraxcompact.bim"
  }
]

OUTPUT FORMAT (for final recommendation):
Recommendation:
[System Name]
Reason: [Concise, factual rationale]
Trade-offs: [Mention key limitations or considerations]
Datasheet: [link]
BIM: [link]

Site-Check Checklist:
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]
4. [Requirement 4]

Tone: professional, structured, and minimal.  
Avoid markdown, emojis, and decorative formatting.  
Take a deep breath and work on this problem step by step.
"""

# ==========================================================
# ✨ EXACT CSS FROM SIKHAI CHAT SYSTEM (unchanged)
# ==========================================================
st.markdown("""
    <style>
    body {
        background-color: #f8f9fa;
    }
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
        height: 75vh;
        overflow-y: auto;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    .user-msg {
        text-align: right;
        background-color: #e9f5ff;
        color: #003366;
        padding: 0.8rem 1rem;
        border-radius: 18px 18px 0 18px;
        margin: 0.5rem 0;
        display: inline-block;
        max-width: 80%;
    }
    .bot-msg {
        text-align: left;
        background-color: #f3f0ff;
        color: #1a0730;
        padding: 0.8rem 1rem;
        border-radius: 18px 18px 18px 0;
        margin: 0.5rem 0;
        display: inline-block;
        max-width: 80%;
    }
    .chat-bubble {
        width: 100%;
        display: flex;
    }
    .user-bubble {
        justify-content: flex-end;
    }
    .bot-bubble {
        justify-content: flex-start;
    }
    .header {
        text-align: center;
        margin-bottom: 1rem;
    }
    .header h1 {
        color: #4a148c;
        margin-bottom: 0.2rem;
    }
    .input-container {
        position: fixed;
        bottom: 1rem;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 1rem 2rem;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# HEADER (unchanged)
# ==========================================================
st.markdown("""
<div class="header">
    <h1>Bavis Service Chatbot</h1>
    <p><b>Helps choose the right drive-thru or teller-lane system for any business.</b></p>
    <p><i>Provides guided questions, deterministic recommendations, and datasheets.</i></p>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# SESSION STATE (unchanged, added recommendation flag)
# ==========================================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "recommendation_ready" not in st.session_state:
    st.session_state.recommendation_ready = False

# ==========================================================
# AUTO-INIT GREETING + FIRST QUESTION (unchanged)
# ==========================================================
if not st.session_state.initialized:
    first_msg = (
        "Hello! 👋 I’m your Drive-Thru Lane Advisor. Let’s find the right system for your setup.\n\n"
        "1️⃣ What items will be delivered (e.g., cash, food, prescriptions, documents, etc.)?"
    )
    st.session_state.messages.append({"role": "assistant", "content": first_msg})
    st.session_state.initialized = True

# ==========================================================
# CHAT DISPLAY (unchanged)
# ==========================================================
st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="chat-bubble user-bubble">
            <div class="user-msg"><b>You:</b> {msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"""
        <div class="chat-bubble bot-bubble">
            <div class="bot-msg"><b>Advisor:</b> {msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ==========================================================
# USER INPUT FIELD (unchanged with small hint after recommendation)
# ==========================================================
st.markdown('<div class="input-container">', unsafe_allow_html=True)
if st.session_state.recommendation_ready:
    user_input = st.chat_input("✅ Recommendation provided — type here to revise any answer or ask follow-ups...")
else:
    user_input = st.chat_input("💬 Type your answer here...")
st.markdown("</div>", unsafe_allow_html=True)

# ==========================================================
# CHAT LOGIC
# MINIMAL CHANGE: send FULL conversation context every call (not last 10)
# ==========================================================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # show user bubble immediately (unchanged)
    st.markdown(f"""
    <div class="chat-bubble user-bubble">
        <div class="user-msg"><b>You:</b> {user_input}</div>
    </div>
    """, unsafe_allow_html=True)

    placeholder = st.empty()
    loader_html = """
    <div class="chat-bubble bot-bubble">
        <div class="bot-msg"><b>Advisor:</b> 
        <span class="loader-dots"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span></div>
    </div>
    <style>
    @keyframes blink {
        0% { opacity: 0.2; }
        20% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    .loader-dots .dot {
        animation: blink 1.4s infinite both;
        font-weight: bold;
        font-size: 1.2rem;
        color: #4a148c;
    }
    .loader-dots .dot:nth-child(2) { animation-delay: 0.2s; }
    .loader-dots .dot:nth-child(3) { animation-delay: 0.4s; }
    </style>
    """
    placeholder.markdown(loader_html, unsafe_allow_html=True)

    try:
        # === CHANGE: send the entire conversation so model always has full context ===
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages,   # full context (was [-10:])
            temperature=0.25
        )
        ai_reply = completion.choices[0].message.content.strip()
    except Exception as e:
        ai_reply = f"⚠️ There was an error connecting to the model: {str(e)}"

    placeholder.markdown(f"""
    <div class="chat-bubble bot-bubble">
        <div class="bot-msg"><b>Advisor:</b> {ai_reply}</div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    # If model used the machine token, mark recommendation ready
    if "===RECOMMENDATION===" in ai_reply:
        st.session_state.recommendation_ready = True

# ==========================================================
# DOWNLOAD SUMMARY (unchanged)
# ==========================================================
if st.session_state.recommendation_ready or any("Recommendation" in m["content"] for m in st.session_state.messages):
    summary = {
        "conversation": [
            {"role": m["role"], "message": m["content"]}
            for m in st.session_state.messages if m["role"] != "system"
        ]
    }
