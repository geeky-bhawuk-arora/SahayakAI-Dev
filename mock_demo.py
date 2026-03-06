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

# --- Custom Styling & CSS (Dynamic Design Requirement / Mobile Look) ---
st.set_page_config(page_title="Sahayak AI", page_icon="🇮🇳", layout="centered")

st.markdown("""
    <style>
    /* Simulate a mobile device container */
    .eczjsme4 { /* This targets the main layout block in newer Streamlit versions */
        max-width: 480px !important;
        margin: 0 auto;
        padding: 2rem 1rem;
        background-color: #f8f9fa;
        border-radius: 30px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.1);
        min-height: 85vh;
        border: 8px solid #2b2b2b;
    }
    
    /* Hide top padding and header */
    header {visibility: hidden;}
    .block-container {padding-top: 1rem;}
    
    /* Modern chat bubbles */
    .stChatMessage {
        background-color: transparent !important;
        padding: 0 !important;
    }
    [data-testid="chatAvatarIcon-user"] {
        background-color: #0b93f6 !important;
    }
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #128c7e !important;
    }
    
    .stChatFloatingInputContainer {
        max-width: 460px;
        margin: 0 auto;
        bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Main UI ---
st.title("🎙️ Sahayak AI")
st.markdown("*Voice-first Govt Scheme Assistant*")

# Sidebar - Mock User Profile
with st.sidebar:
    st.header("👤 Mock User Profile")
    st.markdown("Modify this profile to test different eligibility outcomes.")
    
    state = st.selectbox("State", ["Uttar Pradesh", "Maharashtra", "Bihar", "Punjab"])
    occupation = st.selectbox("Occupation", ["farmer", "student", "unemployed", "government_employee"])
    age = st.number_input("Age", min_value=18, max_value=100, value=35)
    land_acres = st.number_input("Land Holdings (Acres)", min_value=0.0, max_value=20.0, value=2.0)
    income = st.number_input("Annual Income (₹)", min_value=0, max_value=2000000, value=50000, step=10000)
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

    st.divider()
    
    st.subheader("🔒 DPDP Data Privacy")
    st.markdown("Demonstration of DataMasker concealing PII for logging:")
    masked_profile = backend["masker"].safe_log_profile(user_profile)
    masked_profile["masked_aadhaar"] = backend["masker"].mask_aadhaar(aadhaar)
    st.json(masked_profile)


# Chat Interface
st.subheader("💬 Chat with Sahayak")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Voice Simulation / Quick Queries
voice_queries = [
    "--- Use Keyboard (Type Below) ---",
    "नमस्ते",
    "Tell me about PM Kisan",
    "Am I eligible for PMJDY?",
    "verify aadhaar"
]

voice_sim = st.selectbox("🎙️ Simulate Voice Input", voice_queries)
prompt = st.chat_input("Or type here...")

if voice_sim != "--- Use Keyboard (Type Below) ---":
    prompt = voice_sim

# User Input Execution
if getattr(st.session_state, 'last_voice', None) != voice_sim or prompt is not None:
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
                if "PM-KISAN" not in target_scheme:
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
