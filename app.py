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
# ==========================================================
SYSTEM_PROMPT = """
Act like a professional Drive-Thru Lane Advisor chatbot for drive-thru setups of any type (food, pharmacy, retail, bank, or logistics).

GOAL:
Guide the user through exactly five questions to identify the correct drive-thru delivery system, using deterministic filtering based on a static catalog. 

RESPONSE RULES:
1. Ask only the following five numbered questions (Q1–Q5) in strict order. Never add or invent new questions or topics.  
2. If the user's answer is unclear or incomplete, ask one concise clarifying question  
3. Once an answer is clear, move directly to the next question without repeating or confirming previous ones.  
4. Keep full context across turns, ensuring each question depends on previous answers.  
5. When all five inputs are collected and clear, output a structured recommendation section — not delimited with "===" or other symbols, and without asterisks, markdown, or emojis.  
6. The recommendation must include:  
   - Recommended system(s) (1–2 options)  
   - Short rationale explaining the choice and trade-offs  
   - Datasheet and BIM links  
   - A "Site-Check Checklist" with 3–5 validation steps
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
# ✨ EXACT CSS FROM SIKHAI CHAT SYSTEM
# ==========================================================
st.markdown("""
    <style>
    body {
        background-color: #f8f9fa;
    }
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    .chat-wrapper-container {
        max-width: 800px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 0;
    }
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0.5rem 1rem;
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
        margin-bottom: 0;
        max-height: calc(100vh - 300px);
        min-height: 0;
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
        word-wrap: break-word;
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
        word-wrap: break-word;
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
        margin-bottom: 0.5rem;
        margin-top: 0;
    }
    .header h1 {
        color: #4a148c;
        margin-bottom: 0.2rem;
        margin-top: 0;
        font-size: 2rem;
    }
    .header h2 {
        color: #4a148c;
        margin-bottom: 0.2rem;
        margin-top: 0;
        font-size: 1.5rem;
    }
    .header p {
        margin: 0.3rem 0;
    }
    .input-wrapper {
        max-width: 800px;
        margin: 0 auto;
        padding: 0.5rem 1rem;
        background-color: #f8f9fa;
        position: sticky;
        bottom: 0;
        z-index: 100;
        margin-top: 0;
        flex-shrink: 0;
    }
    .stChatInput {
        max-width: 100% !important;
        margin: 0 !important;
    }
    .stChatInput > div {
        max-width: 100% !important;
        margin: 0 !important;
    }
    /* Center all content within tabs */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 0 !important;
    }
    .stTabs [data-baseweb="tab-panel"] > div {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem !important;
    }
    /* Hide Streamlit default elements */
    /* #MainMenu {visibility: hidden;} */
    footer {visibility: hidden;}
    /* header {visibility: hidden;} */
    
    /* Remove extra spacing from Streamlit containers */
    .stTabs [data-baseweb="tab-panel"] > div > div {
        gap: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .element-container {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        padding: 0 !important;
    }
    /* Ensure no gap between chat container and input */
    .chat-wrapper-container > * {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    /* Remove gaps from Streamlit markdown containers */
    .stMarkdown {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }
    /* Remove padding from tab content */
    section[data-testid="stTabs"] {
        padding-top: 0 !important;
    }
    section[data-testid="stTabs"] > div {
        padding-top: 0 !important;
    }
    /* Remove gaps between header and chat container */
    .header + div {
        margin-top: 0 !important;
    }
    /* Ensure chat wrapper starts immediately after header */
    .chat-wrapper-container {
        margin-top: 0.5rem !important;
    }
    /* Remove all default Streamlit block spacing */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    /* Remove gaps in markdown containers inside chat */
    .chat-container .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Ensure chat container content starts at top and fills properly */
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    /* Remove any default spacing from Streamlit elements in chat */
    .chat-container .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Remove spacing from Streamlit columns and containers */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] {
        gap: 0 !important;
    }
    /* Ensure tabs have minimal spacing */
    [data-baseweb="tabs"] {
        margin-bottom: 0 !important;
    }
    </style>
    <script>
    function scrollChatToBottom() {
        const chatContainers = document.querySelectorAll('.chat-container');
        chatContainers.forEach(container => {
            container.scrollTop = container.scrollHeight;
        });
    }
    // Scroll on page load
    window.addEventListener('load', scrollChatToBottom);
    // Scroll after a short delay to ensure content is rendered
    setTimeout(scrollChatToBottom, 100);
    // Use MutationObserver to scroll when new content is added
    const observer = new MutationObserver(scrollChatToBottom);
    document.addEventListener('DOMContentLoaded', function() {
        const chatContainers = document.querySelectorAll('.chat-container');
        chatContainers.forEach(container => {
            observer.observe(container, { childList: true, subtree: true });
        });
    });
    </script>
""", unsafe_allow_html=True)

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Bavis Support AI Assistant",
    page_icon="🤖",
    layout="centered"
)

# ==========================================================
# MAIN HEADER
# ==========================================================
st.markdown("""
<div class="header">
    <h1>Bavis Support AI Assistant</h1>
    <p><b>Helps choose the right drive-thru or teller-lane system for any business.</b></p>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# TAB SELECTION
# ==========================================================
tab1, tab2 = st.tabs(["📋 Product Advisor", "🔍 Support Assistant"])

# ==========================================================
# TAB 1: GUIDED ADVISOR (Existing System)
# ==========================================================
with tab1:
    st.markdown("""
    <div class="header">
        <h2>Product Selection Advisor</h2>
        <p><i>Provides guided questions, deterministic recommendations, and datasheets.</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Session state for Guided Advisor
    if "guided_messages" not in st.session_state:
        st.session_state.guided_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if "guided_initialized" not in st.session_state:
        st.session_state.guided_initialized = False
    if "guided_recommendation_ready" not in st.session_state:
        st.session_state.guided_recommendation_ready = False
    if "guided_loading" not in st.session_state:
        st.session_state.guided_loading = False
    
    # Auto-init greeting + first question
    if not st.session_state.guided_initialized:
        first_msg = (
            "Hello! 👋 I'm your Drive-Thru Lane Advisor. Let's find the right system for your setup.\n\n"
            "1️⃣ What items will be delivered (e.g., cash, food, prescriptions, documents, etc.)?"
        )
        st.session_state.guided_messages.append({"role": "assistant", "content": first_msg})
        st.session_state.guided_initialized = True
    
    # Chat display in centered container with fixed input at bottom
    st.markdown('<div class="chat-wrapper-container">', unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for msg in st.session_state.guided_messages[1:]:
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
    
    # Show loading indicator in chat container
    if st.session_state.guided_loading:
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
        st.markdown(loader_html, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # User input field - fixed at bottom
    #st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
    if st.session_state.guided_recommendation_ready:
        user_input = st.chat_input("✅ Recommendation provided — type here to revise any answer or ask follow-ups...", key="guided_input")
    else:
        user_input = st.chat_input("💬 Type your answer here...", key="guided_input")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat logic - add user message and rerun immediately
    if user_input:
        st.session_state.guided_messages.append({"role": "user", "content": user_input})
        st.session_state.guided_loading = True
        st.rerun()
    
    # Handle API call when loading
    if st.session_state.guided_loading:
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.guided_messages,
                temperature=0.25
            )
            ai_reply = completion.choices[0].message.content.strip()
        except Exception as e:
            ai_reply = f"⚠️ There was an error connecting to the model: {str(e)}"
        
        st.session_state.guided_messages.append({"role": "assistant", "content": ai_reply})
        st.session_state.guided_loading = False
        
        # Check for recommendation
        if "Recommendation:" in ai_reply or "Recommendation" in ai_reply:
            st.session_state.guided_recommendation_ready = True
        
        st.rerun()
    
    # Download summary
    if st.session_state.guided_recommendation_ready or any("Recommendation" in m["content"] for m in st.session_state.guided_messages):
        summary = {
            "conversation": [
                {"role": m["role"], "message": m["content"]}
                for m in st.session_state.guided_messages if m["role"] != "system"
            ]
        }

# ==========================================================
# TAB 2: RAG ASSISTANT (New PDF-based System)
# ==========================================================
with tab2:
    st.markdown("""
    <div class="header">
        <h2>Support Assistant</h2>
        <p><i>Ask questions about products, services, and support.</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Import RAG chat module
    try:
        from pdf_rag_chat import generate_answer
        
        # Session state for RAG Assistant
        if "rag_messages" not in st.session_state:
            st.session_state.rag_messages = []
        if "rag_initialized" not in st.session_state:
            st.session_state.rag_initialized = False
        if "rag_loading" not in st.session_state:
            st.session_state.rag_loading = False
        
        # Auto-init greeting
        if not st.session_state.rag_initialized:
            greeting_msg = (
                "Hello! 👋 I'm your RAG-powered Drive-Thru Assistant. "
                "I can answer questions about drive-thru systems, product specifications, "
                "installation requirements, and more based on our product documentation.\n\n"
                "What would you like to know?"
            )
            st.session_state.rag_messages.append({"role": "assistant", "content": greeting_msg})
            st.session_state.rag_initialized = True
        
        # Chat display in centered container with fixed input at bottom
        st.markdown('<div class="chat-wrapper-container">', unsafe_allow_html=True)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for msg in st.session_state.rag_messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-bubble user-bubble">
                    <div class="user-msg"><b>You:</b> {msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f"""
                <div class="chat-bubble bot-bubble">
                    <div class="bot-msg"><b>Assistant:</b> {msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Show loading indicator in chat container
        if st.session_state.rag_loading:
            loader_html = """
            <div class="chat-bubble bot-bubble">
                <div class="bot-msg"><b>Assistant:</b> 
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
            st.markdown(loader_html, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # User input field - fixed at bottom
        #st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
        user_input = st.chat_input("💬 Ask a question about drive-thru systems...", key="rag_input")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Chat logic - add user message and rerun immediately
        if user_input:
            st.session_state.rag_messages.append({"role": "user", "content": user_input})
            st.session_state.rag_loading = True
            st.rerun()
        
        # Handle API call when loading
        if st.session_state.rag_loading:
            try:
                # Generate answer using RAG
                last_user_msg = st.session_state.rag_messages[-1]["content"]
                ai_reply = generate_answer(last_user_msg, st.session_state.rag_messages[:-1])
            except Exception as e:
                ai_reply = f"⚠️ There was an error: {str(e)}. Please make sure the PDF vector database is set up correctly."
            
            st.session_state.rag_messages.append({"role": "assistant", "content": ai_reply})
            st.session_state.rag_loading = False
            st.rerun()
    
    except ImportError as e:
        st.error(f"⚠️ Error importing RAG modules: {e}")
        st.info("Please ensure all required modules (pdf_rag_chat.py, pdf_retriever.py) are in the same directory.")
    except Exception as e:
        st.error(f"⚠️ Error initializing RAG Assistant: {e}")
