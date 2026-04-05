"""
app.py — Pokédex MCP Chatbot Frontend (Streamlit)

Requires:
    pip install streamlit fastmcp requests openai groq anthropic google-generativeai langgraph python-dotenv
"""

import os
import json
import time
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from backend import PROVIDER_MODELS, get_response, SYSTEM_PROMPT

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PokéBot — Pokédex MCP Chat",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — retro Game Boy aesthetic
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323:wght@400&display=swap');

:root {
    --red: #CC0000;
    --red-dark: #990000;
    --red-light: #FF3333;
    --cream: #F5F0E8;
    --dark: #1A1A2E;
    --darker: #0D0D1A;
    --gray: #8B8B8B;
    --green: #00C851;
    --yellow: #FFD700;
    --blue: #4169E1;
    --purple: #9B59B6;
    --screen-bg: #9BBC0F;
    --screen-dark: #0F380F;
    --border: #333355;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--dark) !important;
    font-family: 'VT323', monospace !important;
}

[data-testid="stAppViewContainer"] {
    background: 
        radial-gradient(ellipse at top left, #2a0a0a 0%, transparent 50%),
        radial-gradient(ellipse at bottom right, #0a0a2a 0%, transparent 50%),
        var(--dark) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a0a0a 0%, #0d0d1a 100%) !important;
    border-right: 3px solid var(--red) !important;
}

[data-testid="stSidebar"] * {
    color: var(--cream) !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    font-family: 'Press Start 2P', monospace !important;
    font-size: 10px !important;
    color: var(--red-light) !important;
    text-shadow: 0 0 8px rgba(204, 0, 0, 0.5) !important;
}

/* Selectboxes and inputs */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stPasswordInput > div > div > input {
    background: #0d0d1a !important;
    border: 2px solid var(--red) !important;
    color: var(--cream) !important;
    font-family: 'VT323', monospace !important;
    font-size: 18px !important;
    border-radius: 4px !important;
}

.stSelectbox > div > div:hover,
.stTextInput > div > div > input:focus,
.stPasswordInput > div > div > input:focus {
    border-color: var(--red-light) !important;
    box-shadow: 0 0 12px rgba(204, 0, 0, 0.4) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--red), var(--red-dark)) !important;
    color: white !important;
    font-family: 'Press Start 2P', monospace !important;
    font-size: 9px !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: all 0.1s !important;
    box-shadow: 3px 3px 0 #660000, 0 0 15px rgba(204,0,0,0.3) !important;
    width: 100% !important;
}

.stButton > button:hover {
    transform: translate(-1px, -1px) !important;
    box-shadow: 4px 4px 0 #660000, 0 0 20px rgba(204,0,0,0.5) !important;
}

.stButton > button:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 1px 1px 0 #660000 !important;
}

/* File Uploader tweaks */
[data-testid="stFileUploader"] {
    background: #0d0d1a !important;
    border: 2px dashed var(--red) !important;
    border-radius: 4px !important;
    padding: 10px !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
}

[data-testid="stChatMessageContent"] {
    font-family: 'VT323', monospace !important;
    font-size: 20px !important;
    line-height: 1.4 !important;
}

/* User bubble */
[data-testid="stChatMessage"][data-testid*="user"] {
    flex-direction: row-reverse !important;
}

/* Chat input */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputTextArea"] textarea {
    background: #0d0d1a !important;
    border: 2px solid var(--red) !important;
    border-radius: 4px !important;
    color: var(--cream) !important;
    font-family: 'VT323', monospace !important;
    font-size: 20px !important;
}

[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInputTextArea"] textarea:focus {
    border-color: var(--red-light) !important;
    box-shadow: 0 0 15px rgba(204, 0, 0, 0.3) !important;
}

/* Spinner */
.stSpinner {
    color: var(--red-light) !important;
}

/* Alert / info boxes */
.stAlert {
    font-family: 'VT323', monospace !important;
    font-size: 18px !important;
    border-radius: 4px !important;
}

/* Divider */
hr {
    border-color: var(--red) !important;
    opacity: 0.4 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--darker); }
::-webkit-scrollbar-thumb { background: var(--red); border-radius: 3px; }

/* Main column padding */
.main .block-container {
    padding-top: 1rem !important;
    max-width: 860px !important;
}

/* Status badge */
.status-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 3px;
    font-family: 'Press Start 2P', monospace;
    font-size: 8px;
    margin-bottom: 8px;
}
.status-online { background: #003300; border: 1px solid var(--green); color: var(--green); }
.status-offline { background: #330000; border: 1px solid var(--red); color: var(--red); }

/* Provider badge colors */
.badge-openai   { color: #10a37f; border-color: #10a37f; background: #001a15; }
.badge-groq     { color: #f55036; border-color: #f55036; background: #1a0500; }
.badge-google   { color: #4285f4; border-color: #4285f4; background: #00061a; }
.badge-anthropic{ color: #cc785c; border-color: #cc785c; background: #1a0a05; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Environment Variable extraction
# ─────────────────────────────────────────────────────────────────────────────

def get_env_api_key(provider_name: str) -> str:
    """Returns the corresponding API key from environment variables based on provider."""
    if provider_name == "OpenAI":
        return os.getenv("OPENAI_API_KEY", "")
    elif provider_name == "Groq":
        return os.getenv("GROQ_API_KEY", "")
    elif provider_name == "Anthropic":
        return os.getenv("ANTHROPIC_API_KEY", "")
    elif provider_name == "Google Gemini":
        return os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    return ""

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

# if "mcp" not in st.session_state:
#     st.session_state.mcp = None

# if "mcp_ready" not in st.session_state:
#     st.session_state.mcp_ready = False


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <div style="font-size: 48px; margin-bottom: 8px;">🔴</div>
        <div style="font-family: 'Press Start 2P', monospace; font-size: 11px; 
                    color: #CC0000; text-shadow: 0 0 10px rgba(204,0,0,0.6);
                    line-height: 1.8;">
            POKÉBOT<br>
            <span style="font-size: 8px; color: #888;">MCP POWERED</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    provider = st.selectbox("⚡ LLM PROVIDER", options=list(PROVIDER_MODELS.keys()), key="provider")
    model = st.selectbox("🧠 MODEL", options=PROVIDER_MODELS[provider], key="model")
    
    # API Key Handling (Fallback to .env)
    env_key = get_env_api_key(provider)
    api_key_input = st.text_input("🔑 API KEY", type="password", placeholder="Enter key or load from .env...")
    api_key = api_key_input.strip() or env_key
    
    if api_key == env_key and env_key:
        st.markdown('<span style="font-size: 11px; color: #00C851;">✅ Loaded from environment variables</span>', unsafe_allow_html=True)
    elif not api_key:
        st.markdown('<span style="font-size: 11px; color: #FF3333;">⚠️ No API key provided</span>', unsafe_allow_html=True)

    st.divider()
    
    # Environment Variables Section
    st.markdown("### ⚙️ ENVIRONMENT")
    
    if st.button("📂 LOAD LOCAL .env"):
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            st.success("Local .env loaded!")
            st.rerun()
        except ImportError:
            st.error("Please install python-dotenv: `pip install python-dotenv`")
            
    uploaded_env = st.file_uploader("Upload external .env", type=["env", "txt"], label_visibility="collapsed")
    if uploaded_env is not None:
        if st.button("📥 APPLY UPLOADED .env"):
            try:
                from dotenv import load_dotenv
                with tempfile.NamedTemporaryFile(delete=False, suffix=".env") as tmp:
                    tmp.write(uploaded_env.getvalue())
                    tmp_path = tmp.name
                load_dotenv(tmp_path, override=True)
                os.unlink(tmp_path)
                st.success("Uploaded .env applied!")
                time.sleep(0.5)
                st.rerun()
            except ImportError:
                st.error("Please install python-dotenv: `pip install python-dotenv`")

    st.divider()

    # MCP Server Status & Controls
    # if st.session_state.mcp_ready:
    #     st.markdown('<span class="status-badge status-online">● MCP SERVER ONLINE</span>', unsafe_allow_html=True)
    # else:
    #     st.markdown('<span class="status-badge status-offline">○ MCP SERVER OFFLINE</span>', unsafe_allow_html=True)

    # if st.button("▶ START MCP SERVER"):
    #     if st.session_state.mcp and st.session_state.mcp_ready:
    #         st.info("Already running!")
    #     else:
    #         with st.spinner("Starting Pokédex MCP server..."):
    #             try:
    #                 mcp = MCPClient   #                 mcp.start()
    #                 st.session_state.mcp = mcp
    #                 st.session_state.mcp_ready = True
    #                 st.rerun()
    #             except Exception as e:
    #                 st.error(f"Failed to start MCP server: {e}")

    # if st.button("■ STOP SERVER"):
    #     if st.session_state.mcp:
    #         st.session_state.mcp.stop()
    #         st.session_state.mcp = None
    #         st.session_state.mcp_ready = False
    #         st.rerun()

    st.divider()

    if st.button("🗑 CLEAR CHAT"):
        st.session_state.messages = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Main chat area
# ─────────────────────────────────────────────────────────────────────────────

provider_badge_class = {
    "OpenAI": "badge-openai",
    "Groq": "badge-groq",
    "Google Gemini": "badge-google",
    "Anthropic": "badge-anthropic",
}.get(provider, "")

st.markdown(f"""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
    <div style="font-family: 'Press Start 2P', monospace; font-size: 14px; 
                color: #CC0000; text-shadow: 0 0 12px rgba(204,0,0,0.5);">
        🔴 POKÉDEX CHAT
    </div>
    <span class="status-badge {provider_badge_class}" style="font-size: 7px; margin-bottom: 0;">
        {provider} / {model}
    </span>
</div>
""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div style="border: 2px solid #CC0000; background: #0d0d1a; border-radius: 6px; padding: 24px; margin: 20px 0; font-family: 'VT323', monospace; font-size: 19px; color: #aaa; line-height: 1.7;">
        <div style="font-family: 'Press Start 2P', monospace; font-size: 10px; color: #CC0000; margin-bottom: 16px;">WELCOME, TRAINER!</div>
        Start the MCP server in the sidebar, provide your API key (or load from .env), then ask me anything!<br><br>
        I can help you:<br>
        🔍 &nbsp;Look up any Pokémon's stats and info<br>
        📋 &nbsp;Register new trainers<br>
        ➕ &nbsp;Add Pokémon to a trainer's collection<br>
        ➖ &nbsp;Remove Pokémon from a collection<br>
        👤 &nbsp;View a trainer's full Pokédex<br><br>
        <span style="color: #666; font-size: 16px;">Pokémon data is live from PokeAPI. Trainer data is stored locally.</span>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    avatar = "🔴" if msg["role"] == "assistant" else "🧢"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# ─────────────────────────────────────────────────────────────────────────────
# Chat input & response
# ─────────────────────────────────────────────────────────────────────────────

if prompt := st.chat_input("Ask about Pokémon or manage your trainer..."):

    # if not st.session_state.mcp_ready:
    #     st.warning("⚠️ Please start the MCP server first (sidebar → START MCP SERVER).")
    #     st.stop()

    if not api_key:
        st.warning("⚠️ Please enter your API key or load it from a .env file.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧢"):
        st.markdown(prompt)

    llm_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    with st.chat_message("assistant", avatar="🔴"):
        with st.spinner("PokéBot is thinking..."):
            try:
                reply = get_response(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    messages=llm_messages,
                    # mcp=st.session_state.mcp,
                )
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except ImportError as e:
                pkg = str(e).split("'")[1] if "'" in str(e) else str(e)
                st.error(f"❌ Missing package: `{pkg}`\n\nInstall it with:\n```\npip install {pkg}\n```")

            except Exception as e:
                err_msg = str(e)
                err_lower = err_msg.lower()
                
                # 429 Rate Limit Handling
                if "429" in err_lower or "rate limit" in err_lower or "too many requests" in err_lower:
                    st.error("⏳ **RATE LIMIT EXCEEDED (429)**\n\nWhoa there, Trainer! You've hit the API rate limit for this provider. Please wait a moment before trying again, or switch to a different LLM provider in the sidebar.")
                # Invalid Key Handling
                elif "api_key" in err_lower or "authentication" in err_lower or "401" in err_lower:
                    st.error("❌ Invalid API key. Please check your key or .env file.")
                else:
                    st.error(f"❌ Error: {err_msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Shell Chat History Injection (Up/Down Arrow Functionality)
# ─────────────────────────────────────────────────────────────────────────────

# Limit history to max 100 messages to prevent excessive load.
user_history = [m["content"] for m in st.session_state.messages if m["role"] == "user"][-100:]

shell_history_js = f"""
<script>
// 1. Send the updated history to the Parent Window (Standard Streamlit UI)
const doc = window.parent.document;
window.parent.chatHistory = {json.dumps(user_history)};
window.parent.historyIndex = window.parent.chatHistory.length;

function attachShellHistory() {{
    const inputs = doc.querySelectorAll('[data-testid="stChatInputTextArea"] textarea, [data-testid="stChatInput"] textarea');
    if (inputs.length === 0) return;
    const chatInput = inputs[0];

    // 2. Only attach event listener once
    if (chatInput && !chatInput.dataset.historyAttached) {{
        chatInput.dataset.historyAttached = 'true';
        
        // React overrides native value setters. We must trigger the native HTML setter.
        function setNativeValue(element, value) {{
            const valueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            const prototype = Object.getPrototypeOf(element);
            const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
            
            if (valueSetter && valueSetter !== prototypeValueSetter) {{
                prototypeValueSetter.call(element, value);
            }} else {{
                valueSetter.call(element, value);
            }}
            // Dispatch input event to inform React of the new value
            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}

        // 3. Listen for Key Events (Up & Down Arrows)
        chatInput.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowUp') {{
                if (window.parent.historyIndex > 0) {{
                    e.preventDefault();
                    window.parent.historyIndex--;
                    setNativeValue(chatInput, window.parent.chatHistory[window.parent.historyIndex]);
                }}
            }} else if (e.key === 'ArrowDown') {{
                if (window.parent.historyIndex < window.parent.chatHistory.length - 1) {{
                    e.preventDefault();
                    window.parent.historyIndex++;
                    setNativeValue(chatInput, window.parent.chatHistory[window.parent.historyIndex]);
                }} else if (window.parent.historyIndex === window.parent.chatHistory.length - 1) {{
                    e.preventDefault();
                    window.parent.historyIndex++;
                    setNativeValue(chatInput, '');
                }}
            }}
        }});
    }}
}}

// Run attempts sequentially to ensure elements are rendered 
attachShellHistory();
setTimeout(attachShellHistory, 500);
setTimeout(attachShellHistory, 1000);
</script>
"""

# Render hidden HTML component containing the script
components.html(shell_history_js, height=0, width=0)