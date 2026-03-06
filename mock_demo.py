import streamlit as st
import os
import sys
import json

# Setup environment for Mock Mode
os.environ["MOCK_MODE"] = "1"
os.environ["BEDROCK_MODEL_ID"] = "mock-model"

# Python Path Setup
project_root = os.path.dirname(os.path.abspath(__file__))
# Add root so `scripts.seed_schemes` can be imported by rule_engine
sys.path.insert(0, project_root)

# Add all service 'src' directories to sys.path
services_dir = os.path.join(project_root, "services")
for svc in os.listdir(services_dir):
    svc_path = os.path.join(services_dir, svc, "src")
    if os.path.isdir(svc_path):
        sys.path.insert(0, svc_path)

# Import backend classes
from processors.language_detector import LanguageDetector
from orchestration.intent_classifier import IntentClassifier
from bedrock.bedrock_client import BedrockOrchestrator
from rules.rule_engine import EligibilityRuleEngine
from privacy.data_masker import DataMasker

# --- Application Initialization ---

@st.cache_resource
def load_backend():
    return {
        "lang_detect": LanguageDetector(),
        "intent_clf": IntentClassifier(),
        "orchestrator": BedrockOrchestrator(),
        "rule_engine": EligibilityRuleEngine(),
        "masker": DataMasker()
    }

backend = load_backend()

# --- Custom Styling & CSS (Phase 7: Massive Scale Custom Dark Branding) ---
st.set_page_config(
    page_title="Sahayak AI - Massive Scale", 
    page_icon="🌌", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Global Custom Dark Theme styling */
    .stApp {
        background-color: #0A0A0A !important; /* Pitch Black/Deep Dark */
        color: #E2E8F0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #E2E8F0 !important;
    }
    
    header {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        max-width: 850px !important; 
    }

    /* Vanguard Proprietary Header */
    .gov-header {
        background: linear-gradient(90deg, #121212 0%, #1A1A1A 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 16px 16px;
        color: white !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #3B82F6; /* Electric Blue Accent */
        position: relative;
        overflow: hidden;
    }
    /* Saffron/Green subtle glow effect */
    .gov-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #FF9933 0%, #3B82F6 50%, #138808 100%);
        opacity: 0.8;
    }
    .gov-header h2 {
        color: #FFFFFF !important;
        margin: 0;
        font-weight: 700;
        font-size: 2rem;
        letter-spacing: 1px;
    }
    .gov-header p {
        color: #94A3B8 !important;
        margin: 0;
        font-size: 0.95rem;
    }
    
    @keyframes fadeInSlideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .central-greeting {
        text-align: center;
        margin-top: 10vh;
        margin-bottom: 2rem;
        animation: fadeInSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    .central-greeting h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
        background: -webkit-linear-gradient(45deg, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Neumorphic Dark Expander */
    [data-testid="stExpander"] {
        background-color: #121212 !important;
        border: 1px solid #2D3748 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    [data-testid="stExpander"] summary {
        color: #A0AEC0 !important;
        font-weight: 500;
    }
    
    .stChatMessage {
        background-color: transparent !important;
        padding: 1.5rem 0 !important;
        border-bottom: 1px solid #2D3748 !important; 
        animation: fadeInSlideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    [data-testid="chatAvatarIcon-user"] {
        display: none;
    }
    [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        color: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.4);
    }
    
    /* Neon Input Box */
    .stChatFloatingInputContainer {
        max-width: 850px !important;
        margin: 0 auto;
        bottom: 40px !important;
        background-color: #121212 !important;
        border-radius: 25px !important;
        border: 1px solid #3B82F6 !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.15) !important;
        padding: 5px 15px !important;
    }
    
    [data-testid="stChatInputTextArea"] {
        color: #FFFFFF !important;
        background-color: transparent !important;
        border: none !important;
        font-size: 1.1rem !important;
    }
    
    [data-testid="stChatInputSubmitButton"] {
        color: #3B82F6 !important;
    }
    
    /* Cyber Pill Buttons */
    .stButton > button {
        background-color: #121212 !important;
        color: #60A5FA !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.1);
    }
    .stButton > button:hover {
        background-color: #3B82F6 !important;
        border-color: #60A5FA !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
        transform: translateY(-1px);
    }
    
    .stHorizontalBlock::-webkit-scrollbar {
        display: none;
    }
    
    hr {
        border-color: #2D3748 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Main UI ---
st.markdown("""
<div class="gov-header">
    <div>
        <h2>Sahayak AI <span style="font-size: 1rem; color: #3B82F6; font-weight: normal; border: 1px solid #3B82F6; padding: 2px 6px; border-radius: 12px; margin-left: 10px;">PRO</span></h2>
        <p>Advanced Proprietary Intelligence Model (60+ Schemes)</p>
    </div>
    <div style="font-size: 2rem;">⚡</div>
</div>
""", unsafe_allow_html=True)

# Top Expander - Mock User Profile (Subtle)
with st.expander("⚙️ System Configuration (Profile & Accessibility)"):
    st.markdown("Modify this profile to test different eligibility outcomes.")
    
    col1, col2 = st.columns(2)
    with col1:
        state = st.selectbox("State", ["Uttar Pradesh", "Maharashtra", "Bihar", "Punjab"])
        occupation = st.selectbox("Occupation", ["farmer", "student", "unemployed", "government_employee"])
        age = st.number_input("Age", min_value=18, max_value=100, value=35)
    with col2:
        land_acres = st.number_input("Land (Acres)", min_value=0.0, max_value=20.0, value=2.0)
        income = st.number_input("Income (₹)", min_value=0, max_value=2000000, value=50000, step=10000)
        aadhaar = st.text_input("Aadhaar Number", "123456789012")
    
    user_profile = {
        "user_id": "mock_user_123",
        "state": state,
        "occupation": occupation,
        "age": age,
        "land_holdings_acres": land_acres,
        "annual_income": income,
        "aadhaar_raw": aadhaar,
        "documents_available": ["aadhaar", "bank_account", "land_records"]
    }

    st.subheader("🔒 DPDP Data Privacy")
    st.markdown("Demonstration of DataMasker concealing PII for logging:")
    masked_profile = backend["masker"].safe_log_profile(user_profile)
    masked_profile["masked_aadhaar"] = backend["masker"].mask_aadhaar(aadhaar)
    st.json(masked_profile)

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Conditional Display: Intro Greeting vs Chat Display
if not st.session_state.messages:
    # Empty state - show sleek minimal greeting exactly like the screenshot
    st.markdown("""
        <div class="central-greeting">
            <h1>नमस्कार! I am Sahayak AI.</h1>
            <p style="font-size: 1.1rem; color: #94A3B8 !important; margin-top: 10px;">Ask me anything. I am powered by a database of over 60+ Central and State Government Schemes.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Voice Simulation / Quick Queries
# Add some spacing to separate from chat
st.write("")
c1, c2, c3, c4, c5, c6 = st.columns(6)
voice_sim = None
with c1:
    if st.button("🎙️ PM-KISAN?"): voice_sim = "Tell me about PM Kisan"
with c2:
    if st.button("🎙️ PMJDY"): voice_sim = "Am I eligible for PMJDY?"
with c3:
    if st.button("🎙️ PM-JAY Health"): voice_sim = "Tell me about Ayushman Bharat"
with c4:
    if st.button("🎙️ Job Guarantee"): voice_sim = "How does NREGA work?"
with c5:
    if st.button("🎙️ UP Education Scheme"): voice_sim = "Tell me about Uttar pradesh education support"
with c6:
    if st.button("🎙️ Maharashtra Startup"): voice_sim = "Maharashtra startup scheme"

prompt = st.chat_input(" Ask Sahayak anything...")

if voice_sim:
    prompt = voice_sim

# User Input Execution
if prompt is not None:
    # Basic deduplication to avoid double run on selectbox change + enter
    if prompt and (getattr(st.session_state, 'last_prompt', None) != prompt):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.last_prompt = prompt
        st.session_state.last_voice = voice_sim
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Listening & Processing..."):
            
                # Formatted History for Intent Classifier and LLM Orchestrator
                history_formatted = [{"user_input": m["content"]} if m["role"] == "user" else {"bot_response": m["content"]} for m in st.session_state.messages[:-1]]
                
                # 1. Language Detection
                lang = backend["lang_detect"].detect(prompt)
                lang_str = "Hindi" if lang == "hi" else "English"
                st.info(f"🌐 **LanguageDetector**: `{lang.upper()}` ({lang_str})")
                
                # 2. Intent Classification
                intent = backend["intent_clf"].classify(prompt, lang, history_formatted)
                st.info(f"🎯 **IntentClassifier**: `{intent.name}` (Confidence: {intent.confidence:.2f})")
                
                # Determine Action based on Intent
                if intent.name == "eligibility_check":
                    st.write("⚙️ **EligibilityRuleEngine**: Evaluating rules locally with Seed Schemes Data...")
                    
                    target_scheme = intent.entities.get("scheme_id", "PM-KISAN-2024")
                    # Fallback mapping for demo purposes
                    if "PMJDY" in target_scheme:
                        target_scheme = "PMJDY-2024"
                    elif "PMJJBY" in target_scheme:
                        target_scheme = "PMJJBY-2024"
                    elif "PMSBY" in target_scheme:
                        target_scheme = "PMSBY-2024"
                    elif "PMJAY" in target_scheme:
                        target_scheme = "PMJAY-2024"
                    elif "PMAY" in target_scheme:
                        target_scheme = "PMAY-G-2024"
                    elif "MGNREGS" in target_scheme:
                        target_scheme = "MGNREGS-2024"
                    elif "PM-KISAN" not in target_scheme:
                         target_scheme = "PM-KISAN-2024" # Default for demo
                         
                    decision = backend["rule_engine"].evaluate(target_scheme, user_profile)
                    
                    # Render decision result
                    if decision.status == "eligible":
                        st.success(f"**Status:** {decision.status.upper()} - {decision.recommendation_en}")
                    else:
                        st.error(f"**Status:** {decision.status.upper()} - {decision.recommendation_en}")
                    
                    with st.expander("View Evaluation Matrix"):
                        for crit in decision.criterion_results:
                            icon = "✅" if crit.status == "pass" else ( "⚠️" if crit.status == "unknown" else "❌" )
                            st.write(f"{icon} **{crit.criterion_name}**: User Value `{crit.user_value}` vs Required `{crit.required_value}`  \n  *{crit.message_en}*")
                            
                    response_text = decision.recommendation_hi if lang == "hi" else decision.recommendation_en
                    
                else:
                    st.write("⚙️ **BedrockOrchestrator**: Bypassed AWS, streaming mock LLM response...")
                    
                    # 3. LLM Orchestrator Mock
                    orchestrator_response = backend["orchestrator"].generate_response(
                        user_query=prompt,
                        language=lang,
                        retrieval_results=[],
                        conversation_history=history_formatted,
                        user_context=user_profile
                    )
                    response_text = orchestrator_response["response_text"]
                    st.write(response_text)
                    if orchestrator_response.get("action_items"):
                         st.write("**Next Steps:**")
                         for item in orchestrator_response["action_items"]:
                             st.write(f"- {item}")
                             
                st.session_state.messages.append({"role": "assistant", "content": response_text})
