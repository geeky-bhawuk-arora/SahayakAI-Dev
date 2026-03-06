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
            time.sleep(1) # Simulate generation latency
            
            query_lower = user_query.lower()
            
            # --- Cross-Questioning Context Resolution ---
            last_scheme = None
            # Scan history backwards to find latest mentioned scheme by the assistant
            for msg in reversed(conversation_history):
                if "bot_response" in msg:
                    resp = msg["bot_response"].lower()
                    if "pm kisan" in resp: last_scheme = "PM-KISAN-2024"
                    elif "jan dhan" in resp or "pmjdy" in resp: last_scheme = "PMJDY-2024"
                    elif "jeevan jyoti" in resp or "pmjjby" in resp: last_scheme = "PMJJBY-2024"
                    elif "suraksha bima" in resp or "pmsby" in resp: last_scheme = "PMSBY-2024"
                    elif "ayushman" in resp or "pm-jay" in resp: last_scheme = "PMJAY-2024"
                    elif "pmay" in resp or "awaas" in resp: last_scheme = "PMAY-G-2024"
                    elif "mgnregs" in resp or "nrega" in resp: last_scheme = "MGNREGS-2024"
                    
                    if last_scheme: break

            # 1. Follow-up / Cross-Questioning (Multi-Turn)
            is_followup = False
            followup_intent = None
            if any(word in query_lower for word in ["how", "apply", "process", "कैसे आवेदन"]): 
                is_followup, followup_intent = True, "application_process"
            elif any(word in query_lower for word in ["documents", "doc", "what do i need", "दस्तावेज़", "जरूरत"]): 
                is_followup, followup_intent = True, "documents_required"
            elif query_lower in ["yes", "yeah", "check", "हां", "जी हां"] and last_scheme:
                # Triggered eligibility check flow visually via UI text recommendation
                text_en = f"Great! I am initializing the Eligibility Rule Engine for the {last_scheme.split('-')[0]} scheme now..."
                text_hi = f"बहुत बढ़िया! मैं अब {last_scheme.split('-')[0]} योजना के लिए पात्रता नियम इंजन शुरू कर रहा हूँ..."
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": [last_scheme], "action_items": ["Running rule engine"], "needs_more_info": [], "confidence": 0.99}

            if is_followup and last_scheme:
                if followup_intent == "application_process":
                    text_en = f"To apply for {last_scheme.split('-')[0]}, you generally need to visit the respective official portal or your local Gram Panchayat / CSC center. Would you like me to check your profile eligibility first to ensure you qualify before applying?"
                    text_hi = f"{last_scheme.split('-')[0]} के लिए आवेदन करने के लिए, आपको आम तौर पर संबंधित आधिकारिक पोर्टल या अपने स्थानीय ग्राम पंचायत / सीएससी केंद्र पर जाना होगा। क्या आवेदन करने से पहले आप अपनी प्रोफ़ाइल की पात्रता की जांच करना चाहेंगे?"
                else:
                    text_en = f"For the {last_scheme.split('-')[0]} scheme, you will typically need your Aadhaar Card, Bank Account details, and a passport-sized photograph. Some schemes also require Income Certificates. Want me to check your eligibility based on these?"
                    text_hi = f"{last_scheme.split('-')[0]} योजना के लिए, आपको आमतौर पर अपना आधार कार्ड, बैंक खाता विवरण और एक पासपोर्ट आकार का फोटोग्राफ चाहिए होगा। कुछ योजनाओं के लिए आय प्रमाण पत्र की भी आवश्यकता होती है। क्या आप चाहते हैं कि मैं आपकी पात्रता की जांच करूं?"
                
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": [last_scheme], "action_items": ["Gather required documents"], "needs_more_info": [], "confidence": 0.95}

            # 2. Check for greetings
            if query_lower in ["hello", "hi", "hey", "नमस्ते"]:
                text_en = "Hello there! 👋 I am Sahayak AI, your personal government scheme assistant. I'm here to help you access schemes easily using just your voice. You can ask me about schemes or check your eligibility. How can I assist you today?"
                text_hi = "नमस्ते! 👋 मैं सहायक एआई हूँ, आपका व्यक्तिगत सरकारी योजना सहायक। मैं आपकी आवाज़ का उपयोग करके योजनाओं तक आसानी से पहुँचने में मदद करने के लिए यहाँ हूँ। आप मुझसे योजनाओं के बारे में पूछ सकते हैं या अपनी पात्रता की जांच कर सकते हैं। आज मैं आपकी कैसे सहायता कर सकता हूँ?"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": [], "action_items": [], "needs_more_info": [], "confidence": 0.99}

            # 3. Base Scheme Info Queries (Phase 6 full data with sources)
            if "kisan" in query_lower or "pm kisan" in query_lower or "किसान" in query_lower:
                text_en = "Ah, PM-KISAN! That's a great initiative. 🌾 It provides an income support of exactly ₹6,000 per year to all land-holding farmer families in India, transferred directly to your bank account. Should we check if you are eligible?\n\n*Source: https://pmkisan.gov.in*"
                text_hi = "अच्छा, पीएम-किसान! यह किसानों के लिए एक बहुत अच्छी योजना है। 🌾 इसके तहत सभी भूमिधारी किसान परिवारों को खेती के खर्च के लिए प्रति वर्ष 6000 रुपये की आय सहायता दी जाती है। क्या हम जांचें कि आप पात्र हैं या नहीं?\n\n*स्रोत: https://pmkisan.gov.in*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": ["PM-KISAN-2024"], "action_items": ["Verify your Aadhaar via voice", "Link your bank account"], "needs_more_info": [], "confidence": 0.99}
            
            elif "jan dhan" in query_lower or "pmjdy" in query_lower or "जन धन" in query_lower:
                text_en = "Oh, certainly! 🏦 The Pradhan Mantri Jan Dhan Yojana (PMJDY) helps you open a digital bank account with absolute zero balance. To add to that, it also comes with an accident insurance cover of ₹2 lakh! Would you like help applying?\n\n*Source: https://pmjdy.gov.in*"
                text_hi = "जी बिल्कुल! 🏦 यदि आपका बैंक में खाता नहीं है तो प्रधानमंत्री जन धन योजना (PMJDY) बहुत बढ़िया है। यह आपको जीरो बैलेंस पर बैंक खाता खोलने में मदद करती है, और इसमें 2 लाख रुपये का दुर्घटना बीमा भी मिलता है! क्या आप इसके लिए आवेदन करना चाहेंगे?\n\n*स्रोत: https://pmjdy.gov.in*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": ["PMJDY-2024"], "action_items": ["Visit your nearest local bank branch", "Provide e-KYC via Aadhaar"], "needs_more_info": [], "confidence": 0.99}
            
            elif "jeevan jyoti" in query_lower or "pmjjby" in query_lower or "life insurance" in query_lower or "जीवन ज्योति" in query_lower:
                text_en = "Absolutely! ❤️ The Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY) offers a 1-year renewable life insurance cover of ₹2 lakh for any cause of death at a premium of just ₹436/year. Should I check your age eligibility?\n\n*Source: https://jansuraksha.gov.in/Forms-PMJJBY.aspx*"
                text_hi = "बिल्कुल! ❤️ प्रधानमंत्री जीवन ज्योति बीमा योजना (PMJJBY) किसी भी कारण से मृत्यु के लिए ₹2 लाख का 1 साल का नवीकरणीय जीवन बीमा कवर प्रदान करती है। इसका प्रीमियम केवल ₹436/वर्ष है। क्या मैं जांच करूं कि आपकी आयु इसके लिए योग्य है?\n\n*स्रोत: https://jansuraksha.gov.in/Forms-PMJJBY.aspx*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": ["PMJJBY-2024"], "action_items": ["Link your bank account", "Set up auto-debit for premium"], "needs_more_info": [], "confidence": 0.98}
            
            elif "suraksha bima" in query_lower or "pmsby" in query_lower or "accident insurance" in query_lower or "सुरक्षा बीमा" in query_lower:
                text_en = "Got it! 🛡️ Pradhan Mantri Suraksha Bima Yojana (PMSBY) provides accidental death and disability cover of ₹2 lakh for just ₹20 per year! Want to know the enrollment process details?\n\n*Source: https://jansuraksha.gov.in/Forms-PMSBY.aspx*"
                text_hi = "समझ गया! 🛡️ प्रधानमंत्री सुरक्षा बीमा योजना (PMSBY) ₹2 लाख का दुर्घटना मृत्यु और विकलांगता कवर प्रदान करती है, वह भी केवल ₹20 प्रति वर्ष के प्रीमियम के साथ! क्या आप नामांकन प्रक्रिया के बारे में अधिक जानना चाहते हैं?\n\n*स्रोत: https://jansuraksha.gov.in/Forms-PMSBY.aspx*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": ["PMSBY-2024"], "action_items": ["Visit your bank branch", "Sign auto-debit form"], "needs_more_info": [], "confidence": 0.98}
            
            elif "ayushman" in query_lower or "pmjay" in query_lower or "health insurance" in query_lower or "आयुष्मान" in query_lower:
                text_en = "Health is wealth! 🏥 Ayushman Bharat (PM-JAY) provides a massive health cover of ₹5 lakhs per family per year for secondary and tertiary care hospitalization. Let's check your family's eligibility for this!\n\n*Source: https://pmjay.gov.in*"
                text_hi = "स्वास्थ्य ही धन है! 🏥 आयुष्मान भारत (PM-JAY) अस्पताल में भर्ती के लिए प्रति परिवार प्रति वर्ष ₹5 लाख का कवर प्रदान करती है। क्या हम इसके लिए आपकी पात्रता की जांच करें?\n\n*स्रोत: https://pmjay.gov.in*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": ["PMJAY-2024"], "action_items": ["Check your ration card status", "Visit an empanelled hospital"], "needs_more_info": [], "confidence": 0.99}
            
            elif "awaas" in query_lower or "housing" in query_lower or "pmay" in query_lower or "आवास" in query_lower:
                text_en = "A home for everyone! 🏠 Pradhan Mantri Awaas Yojana - Gramin (PMAY-G) provides a pucca house with basic amenities to houseless families and those living in kutcha houses in rural areas. Financial assistance up to ₹1.2 Lakh is provided. Shall we see if you meet the housing criteria?\n\n*Source: https://pmayg.nic.in*"
                text_hi = "सबके लिए घर! 🏠 प्रधानमंत्री आवास योजना - ग्रामीण (PMAY-G) ग्रामीण क्षेत्रों में बेघर परिवारों को पक्का घर प्रदान करती है। ₹1.2 लाख तक की वित्तीय सहायता दी जाती है। क्या हम देखें कि आप आवास मानदंड को पूरा करते हैं या नहीं?\n\n*स्रोत: https://pmayg.nic.in*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": ["PMAY-G-2024"], "action_items": ["Verify Job Card", "Gather rural housing records"], "needs_more_info": [], "confidence": 0.99}
            
            elif "mgnrega" in query_lower or "nrega" in query_lower or "employment" in query_lower or "रोजगार" in query_lower or "मनरेगा" in query_lower:
                text_en = "Certainly. 💼 Mahatma Gandhi National Rural Employment Guarantee Scheme (MGNREGS) guarantees 100 days of wage employment in a financial year to rural adults willing to do unskilled manual work. Do you have a job card yet?\n\n*Source: https://nrega.nic.in*"
                text_hi = "ज़रूर। 💼 मनरेगा (MGNREGS) एक वित्तीय वर्ष में 100 दिनों के मजदूरी रोजगार की गारंटी देता है। क्या आपके पास जॉब कार्ड है?\n\n*स्रोत: https://nrega.nic.in*"
                text = text_hi if language == "hi" else text_en
                return {"response_text": text, "schemes_mentioned": ["MGNREGS-2024"], "action_items": ["Apply for a Job Card at Gram Panchayat"], "needs_more_info": [], "confidence": 0.99}
                
            else:
                text_en = "I'm not quite sure about that in this local demo mode. 😅 You can ask me about **PM Kisan**, **Jan Dhan**, **Life/Health Insurance**, **Rural Housing**, or **Employment (NREGA)**, or try following up on previous questions like 'How do I apply?'!"
                text_hi = "मैं इस स्थानीय डेमो मोड में इसके बारे में सुनिश्चित नहीं हूँ। 😅 आप मुझसे **पीएम किसान**, **जन धन**, **जीवन/स्वास्थ्य बीमा**, **ग्रामीण आवास**, या **रोजगार (नरेगा)** के बारे में पूछ सकते हैं, या 'मैं आवेदन कैसे करूं?' जैसे अनुवर्ती प्रश्न आज़मा सकते हैं!"
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
