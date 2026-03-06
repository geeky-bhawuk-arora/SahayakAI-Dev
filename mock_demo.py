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

# --- Custom Styling & CSS (Phase 6: National Scale GovTech Brand UI) ---
st.set_page_config(
    page_title="Sahayak AI - Government of India", 
    page_icon="🇮🇳", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Global GovTech Light Theme styling */
    .stApp {
        background-color: #F8F9FA !important; /* Extremely light off-white/grey for readability */
        color: #212529 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    /* Override Streamlit text colors for light mode */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #212529 !important;
    }
    
    /* Hide native header and adjust padding */
    header {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        max-width: 850px !important; 
    }

    /* Official National Header */
    .gov-header {
        background-color: #0F4C81; /* Deep Official Blue */
        padding: 1.5rem 2rem;
        border-radius: 0 0 12px 12px;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 4px solid #FF9933; /* Saffron Accent */
    }
    .gov-header h2 {
        color: white !important;
        margin: 0;
        font-weight: 600;
        font-size: 1.8rem;
    }
    .gov-header p {
        color: #E2E8F0 !important;
        margin: 0;
        font-size: 0.9rem;
    }
    
    /* Smooth intro animation */
    @keyframes fadeInSlideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* The large central greeting */
    .central-greeting {
        text-align: center;
        margin-top: 10vh; /* Push down to center */
        margin-bottom: 2rem;
        animation: fadeInSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    .central-greeting h1 {
        font-size: 2.2rem !important;
        font-weight: 600 !important;
        color: #0F4C81 !important;
        letter-spacing: -0.5px;
    }
    
    /* Streamlit's native Expander Styling */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    [data-testid="stExpander"] summary {
        color: #4A5568 !important;
        font-weight: 500;
    }
    
    /* Chat message area */
    .stChatMessage {
        background-color: transparent !important;
        padding: 1.5rem 0 !important;
        border-bottom: 1px solid #E2E8F0 !important; 
        animation: fadeInSlideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    /* Hide default user icon, style assistant icon */
    [data-testid="chatAvatarIcon-user"] {
        display: none;
    }
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #0F4C81 !important; /* Official Blue */
        color: white;
        border-radius: 4px;
    }
    
    /* The Floating Pill Input Box Override */
    .stChatFloatingInputContainer {
        max-width: 850px !important;
        margin: 0 auto;
        bottom: 40px !important;
        background-color: #FFFFFF !important;
        border-radius: 25px !important;
        border: 2px solid #E2E8F0 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
        padding: 5px 15px !important;
    }
    
    /* Input field text color */
    [data-testid="stChatInputTextArea"] {
        color: #212529 !important;
        background-color: transparent !important;
        border: none !important;
        font-size: 1.1rem !important; /* Larger text for accessibility */
    }
    
    /* Send button icon coloring */
    [data-testid="stChatInputSubmitButton"] {
        color: #0F4C81 !important;
    }
    
    /* Pill quick action buttons */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #0F4C81 !important;
        border: 1px solid #CBD5E0 !important;
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stButton > button:hover {
        background-color: #F7FAFC !important;
        border-color: #0F4C81 !important;
        color: #0F4C81 !important;
    }
    
    /* Hide horizontal scrollbar for pills */
    .stHorizontalBlock::-webkit-scrollbar {
        display: none;
    }
    
    hr {
        border-color: #E2E8F0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Main UI ---
st.markdown("""
<div class="gov-header">
    <div>
        <h2>Sahayak AI</h2>
        <p>National Multilingual Govt Scheme Assistant</p>
    </div>
    <div style="font-size: 2rem;">🇮🇳</div>
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
            <h1>नमस्कार! How can I assist you today?</h1>
            <p style="font-size: 1.1rem; color: #4A5568 !important; margin-top: 10px;">I can help you find and apply for over 300+ Government Schemes entirely through conversation.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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
    if st.button("🎙️ PMJJBY/PMSBY"): voice_sim = "What is PMJJBY?"
with c4:
    if st.button("🎙️ PM-JAY Health"): voice_sim = "Tell me about Ayushman Bharat"
with c5:
    if st.button("🎙️ Rural Housing"): voice_sim = "I need a house under PMAY"
with c6:
    if st.button("🎙️ Job Guarantee"): voice_sim = "How does NREGA work?"

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
