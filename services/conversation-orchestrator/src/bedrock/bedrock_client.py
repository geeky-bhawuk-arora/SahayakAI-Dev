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

    def generate_response(
        self,
        user_query: str,
        language: str,
        retrieval_results: List[Dict],
        conversation_history: List[Dict],
        user_context: Dict,
    ) -> Dict:
        if os.environ.get("MOCK_MODE") == "1":
            import time
            time.sleep(1) # simulate latency
            query_lower = user_query.lower()
            
            # 1. Check for greetings
            if "hello" in query_lower or "hi " in query_lower or query_lower == "hi" or "नमस्ते" in query_lower or "hey" in query_lower:
                text_en = "Hello! I am Sahayak AI, your personal government scheme assistant. I'm here to help you access schemes easily using your voice. How can I help you today?"
                text_hi = "नमस्ते! मैं सहायक एआई हूँ, आपका व्यक्तिगत सरकारी योजना सहायक। मैं आपकी आवाज़ का उपयोग करके योजनाओं तक आसानी से पहुँचने में मदद करने के लिए यहाँ हूँ। मैं आज आपकी कैसे मदद कर सकता हूँ?"
                text = text_hi if language == "hi" else text_en
                return {
                    "response_text": text,
                    "schemes_mentioned": [],
                    "action_items": [],
                    "needs_more_info": [],
                    "confidence": 0.99
                }

            # 2. Scheme info queries
            if "kisan" in query_lower or "pm" in query_lower or "किसान" in query_lower:
                text_en = "Sure, I can tell you about PM Kisan. It provides an income support of ₹6,000 per year to all land-holding farmer families in India. The amount is transferred directly to your registered bank account in three equal installments."
                text_hi = "ज़रूर, मैं आपको पीएम-किसान योजना के बारे में बता सकता हूँ। इसके तहत सभी भूमिधारी किसान परिवारों को प्रति वर्ष 6000 रुपये की आय सहायता दी जाती है, जो तीन किश्तों में सीधे खाते में आती है।"
                text = text_hi if language == "hi" else text_en
                return {
                    "response_text": text,
                    "schemes_mentioned": ["PM-KISAN-2024"],
                    "action_items": ["Verify your Aadhaar via voice", "Link your bank account"],
                    "needs_more_info": [],
                    "confidence": 0.99
                }
            elif "jan dhan" in query_lower or "pmjdy" in query_lower or "जन धन" in query_lower:
                text_en = "Certainly! The Pradhan Mantri Jan Dhan Yojana (PMJDY) helps you open a digital bank account with zero balance. It also comes with an overdraft facility and an accident insurance cover of ₹2 lakh."
                text_hi = "जी हाँ! प्रधानमंत्री जन धन योजना (PMJDY) आपको जीरो बैलेंस पर बैंक खाता खोलने में मदद करती है। इसमें ओवरड्राफ्ट और 2 लाख रुपये का दुर्घटना बीमा भी मिलता है।"
                text = text_hi if language == "hi" else text_en
                return {
                    "response_text": text,
                    "schemes_mentioned": ["PMJDY-2024"],
                    "action_items": ["Visit your nearest local bank branch", "Provide e-KYC via Aadhaar"],
                    "needs_more_info": [],
                    "confidence": 0.99
                }
            else:
                text_en = "I am currently in a local demo mode! To see me in action, ask me to 'Tell me about PM Kisan', 'Tell me about Jan Dhan', or simply say 'Hello!'"
                text_hi = "मैं अभी डेमो मोड में हूँ! मुझे काम करते देखने के लिए, 'पीएम किसान के बारे में बताओ', 'जन धन के बारे में बताओ' या बस 'नमस्ते' कहें!"
                text = text_hi if language == "hi" else text_en
                return {
                    "response_text": text,
                    "schemes_mentioned": [],
                    "action_items": [],
                    "needs_more_info": [],
                    "confidence": 0.9
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
