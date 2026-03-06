"""
Bedrock Orchestrator — LLM response generation with RAG context injection.
Uses Claude 3 Sonnet for balanced quality/cost/speed.
Anti-hallucination: responses grounded strictly in retrieved context.
"""
import boto3
import json
import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")


class BedrockOrchestrator:
    def __init__(self):
        if os.environ.get("MOCK_MODE") != "1":
            self.bedrock = boto3.client("bedrock-runtime", region_name="ap-south-1")

    def generate_response(self, user_query: str, language: str, retrieval_results: List[Dict], conversation_history: List[Dict], user_context: Dict = None) -> Dict:
        """Mock Bedrock call that fakes conversational delay and returns synthetic LLM output with multi-turn support."""
        if os.environ.get("MOCK_MODE") == "1":
            import time
            import sys
            time.sleep(1) # Simulate generation latency
            
            # Load schemes dynamically
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
            from scripts.seed_schemes import SCHEMES
            from src.orchestration.intent_classifier import SCHEME_ENTITIES
            
            query_lower = user_query.lower()
            
            # --- Cross-Questioning Context Resolution ---
            last_scheme = None
            # Scan history backwards
            for msg in reversed(conversation_history):
                if "bot_response" in msg:
                    resp = msg["bot_response"]
                    # Check if any scheme entity is mentioned in the bot response
                    for scheme_id, keywords in SCHEME_ENTITIES.items():
                        if any(kw in resp.lower() for kw in keywords if len(kw) > 3) or scheme_id in resp:
                            last_scheme = scheme_id
                            break
                    if last_scheme: break

            # 1. Follow-up / Cross-Questioning (Multi-Turn)
            is_followup = False
            followup_intent = None
            if any(word in query_lower for word in ["how", "apply", "process", "कैसे आवेदन"]): 
                is_followup, followup_intent = True, "application_process"
            elif any(word in query_lower for word in ["documents", "doc", "what do i need", "दस्तावेज़", "जरूरत"]): 
                is_followup, followup_intent = True, "documents_required"
            elif any(word in query_lower for word in ["yes", "yeah", "yup", "yep", "check", "हां", "जी हां"]) and last_scheme:
                text_en = f"Great! I am initializing the Eligibility Rule Engine for the {last_scheme.split('-')[0]} scheme now..."
                text_hi = f"बहुत बढ़िया! मैं अब {last_scheme.split('-')[0]} योजना के लिए पात्रता नियम इंजन शुरू कर रहा हूँ..."
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": [last_scheme], "action_items": ["Running rule engine"], "needs_more_info": [], "confidence": 0.99}

            if is_followup and last_scheme:
                matched_scheme_obj = next((s for s in SCHEMES if s["scheme_id"] == last_scheme), None)
                if matched_scheme_obj:
                    # Dynamically check what documents the scheme actually needs
                    docs = matched_scheme_obj.get("required_documents", ["aadhaar"])
                    docs_str = ", ".join([d.replace('_', ' ').title() for d in docs])
                    url = matched_scheme_obj.get("application_url", "")
                    
                    if followup_intent == "application_process":
                        text_en = f"To apply for {last_scheme.split('-')[0]}, you need to visit the respective official portal at {url}. Would you like me to check your profile eligibility first?"
                        text_hi = f"{last_scheme.split('-')[0]} के लिए आवेदन करने के लिए, आपको {url} पर आधिकारिक पोर्टल पर जाना होगा। क्या मैं पहले आपकी प्रोफ़ाइल पात्रता की जांच करूँ?"
                    else:
                        text_en = f"For the {last_scheme.split('-')[0]} scheme, you will specifically need: **{docs_str}**. Want me to check your eligibility based on these?"
                        text_hi = f"{last_scheme.split('-')[0]} योजना के लिए, आपको विशेष रूप से आवश्यक होगा: **{docs_str}**। क्या आप चाहते हैं कि मैं इन दस्तावेज़ों के आधार पर आपकी पात्रता की जांच करूं?"
                    
                    text = text_hi if language == "hi" else text_en
                    return {"response_text": text, "schemes_mentioned": [last_scheme], "action_items": ["Gather required documents"], "needs_more_info": [], "confidence": 0.95}

            # 2. Check for greetings
            if query_lower in ["hello", "hi", "hey", "नमस्ते"]:
                text_en = f"Hello there! 👋 I am Sahayak AI. I currently hold an active database of **{len(SCHEMES)}+ Government Schemes** across State and Central levels! How can I assist you today?"
                text_hi = f"नमस्ते! 👋 मैं सहायक एआई हूँ। मेरे पास वर्तमान में राज्य और केंद्रीय स्तर पर **{len(SCHEMES)}+ सरकारी योजनाओं** का एक सक्रिय डेटाबेस है! आज मैं आपकी कैसे सहायता कर सकता हूँ?"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": [], "action_items": [], "needs_more_info": [], "confidence": 0.99}

            # 3. Dynamic Scheme Info Queries (Matches against all 60+ schemes based on keywords)
            matched_scheme = None
            for scheme_id, keywords in SCHEME_ENTITIES.items():
                 # Sort keywords by length to match multi-word phrases first ("pm kisan" before "kisan")
                 for kw in sorted(keywords, key=len, reverse=True):
                     if kw in query_lower and len(kw) > 3:
                         matched_scheme = next((s for s in SCHEMES if s["scheme_id"] == scheme_id), None)
                         break
                 if matched_scheme: break

            if matched_scheme:
                scheme_id = matched_scheme["scheme_id"]
                name = matched_scheme["name_en"]
                name_hi = matched_scheme["name_hi"]
                desc_en = matched_scheme["description_en"]
                desc_hi = matched_scheme["description_hi"]
                url = matched_scheme.get("application_url", "")
                
                text_en = f"I found exactly what you are looking for! 📋 **{name}**\n\n{desc_en}\n\nShall we initialize the eligibility engine for this scheme right now?\n\n*Source: {url}*"
                text_hi = f"मुझे ठीक वही मिला है जो आप खोज रहे थे! 📋 **{name_hi}**\n\n{desc_hi}\n\nक्या हम अभी इस योजना के लिए पात्रता इंजन शुरू करें?\n\n*स्रोत: {url}*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": [scheme_id], "action_items": ["Verify KYC to check eligibility"], "needs_more_info": [], "confidence": 0.98}

            # Fallback
            text_en = f"I'm not quite sure. I hold data for **{len(SCHEMES)} schemes**. Try asking me specifically about 'Maharashtra education scheme', 'Bihar agriculture', or 'PM Kisan'!"
            text_hi = f"मैं पूरी तरह आश्वस्त नहीं हूँ। मेरे पास **{len(SCHEMES)} योजनाओं** का डेटा है। मुझसे विशेष रूप से 'महाराष्ट्र शिक्षा योजना', 'बिहार कृषि', या 'पीएम किसान' के बारे में पूछने का प्रयास करें!"
            text = text_hi if language == "hi" else text_en
            return {
                "response_text": text,
                "schemes_mentioned": [],
                "action_items": [],
                "needs_more_info": [],
                "confidence": 0.50
            }

        system_prompt = self._build_system_prompt(language, user_context)
        rag_context = self._format_rag_context(retrieval_results)
        messages = self._build_messages(conversation_history, user_query, rag_context)

        try:
            response = self.bedrock.invoke_model(
                modelId=MODEL_ID,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": messages,
                    "temperature": 0.1,
                    "top_p": 0.9,
                }),
            )
            raw = json.loads(response["body"].read())["content"][0]["text"]
            return self._parse_response(raw)
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}")
            return self._fallback_response(language)

    def _build_system_prompt(self, language: str, user_context: Dict) -> str:
        lang_instruction = (
            "Respond ONLY in Hindi (Devanagari). Use simple language a rural citizen can understand."
            if language == "hi"
            else "Respond in clear, simple English."
        )
        return f"""You are Sahayak AI, a trusted government scheme assistant for Indian citizens.

CRITICAL ANTI-HALLUCINATION RULES:
1. Answer ONLY from the <context> provided. Never invent facts.
2. If info is absent from context, say: "मुझे इस बारे में पक्की जानकारी नहीं है" (hi) or "I don't have verified information on this" (en).
3. Never guess benefit amounts, deadlines, or eligibility criteria.
4. Always name the specific scheme you are referencing.
5. If asked about non-government topics, politely redirect.

LANGUAGE: {lang_instruction}

USER PROFILE:
- State: {user_context.get("state", "Unknown")}
- Occupation: {user_context.get("occupation", "Unknown")}  
- Age: {user_context.get("age", "Unknown")}
- Income: {user_context.get("annual_income", "Unknown")}

OUTPUT FORMAT (strict JSON):
{{
  "response_text": "<your response>",
  "schemes_mentioned": ["scheme_id_1"],
  "action_items": ["Step 1: ...", "Step 2: ..."],
  "needs_more_info": ["field_needed_1"],
  "confidence": 0.95
}}"""

    def _format_rag_context(self, results: List[Dict]) -> str:
        if not results:
            return "<context>No verified scheme information found for this query.</context>"
        parts = ["<context>"]
        for i, r in enumerate(results[:5], 1):
            scheme_name = r.get("scheme_name", "Unknown Scheme")
            text = r.get("text", r.get("content", ""))
            source = r.get("source_url", "")
            parts.append(f'<scheme id="{i}" name="{scheme_name}" source="{source}">{text}</scheme>')
        parts.append("</context>")
        return "\n".join(parts)

    def _build_messages(self, history: List[Dict], query: str, rag_context: str) -> List[Dict]:
        messages = []
        for turn in history[-5:]:
            if turn.get("user_input"):
                messages.append({"role": "user", "content": turn["user_input"]})
            if turn.get("bot_response"):
                messages.append({"role": "assistant", "content": turn["bot_response"]})
        messages.append({"role": "user", "content": f"{rag_context}\n\nQuestion: {query}"})
        return messages

    def _parse_response(self, raw: str) -> Dict:
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
        return {"response_text": raw, "schemes_mentioned": [], "action_items": [], "needs_more_info": [], "confidence": 0.5}

    def _fallback_response(self, language: str) -> Dict:
        text = (
            "माफ़ करें, अभी जवाब देने में समस्या हो रही है। कृपया कुछ देर बाद पुनः प्रयास करें।"
            if language == "hi"
            else "Sorry, I'm having trouble responding right now. Please try again shortly."
        )
        return {"response_text": text, "schemes_mentioned": [], "action_items": [], "needs_more_info": [], "confidence": 0.0}
