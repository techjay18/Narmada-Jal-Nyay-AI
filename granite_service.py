"""
IBM Granite LLM integration via IBM watsonx.ai

ARCHITECTURE PRINCIPLE:
- Deterministic algorithms handle all numerical calculations
- Granite handles reasoning, explanation, and natural-language generation only
"""
from __future__ import annotations
import os
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
GRANITE_MODEL_ID   = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")

# Generation parameters
GENERATE_PARAMS = {
    "max_new_tokens": 512,
    "min_new_tokens": 20,
    "temperature": 0.3,
    "top_p": 0.9,
    "repetition_penalty": 1.1,
    "stop_sequences": ["<|endoftext|>"],
}

_model = None

def _get_model():
    """Lazy-initialise the watsonx model."""
    global _model
    if _model is not None:
        return _model

    if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
        return None  # Fall back to offline mode

    try:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        credentials = Credentials(
            api_key=WATSONX_API_KEY,
            url=WATSONX_URL,
        )
        _model = ModelInference(
            model_id=GRANITE_MODEL_ID,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
            params=GENERATE_PARAMS,
        )
    except Exception as e:
        print(f"[Granite] Failed to initialise watsonx model: {e}")
        _model = None

    return _model


# ─── Fallback responses (for demo without API key) ───────────────────────────

FALLBACK_RESPONSES: Dict[str, str] = {
    "farmer_alert": (
        "Dear Farmer, your irrigation slot is scheduled. "
        "Please prepare your field and open the field channel at the specified time. "
        "Allocated water quantity has been calculated based on your crop and land area."
    ),
    "shortage_explanation": (
        "Canal water availability has reduced by 18% today due to lower upstream inflow. "
        "The system has recalculated allocations using a fairness-weighted algorithm to ensure "
        "tail-end farmers receive priority support. Your revised allocation ensures minimum "
        "crop water requirements are met."
    ),
    "complaint_analysis": (
        "Based on the complaint and current distribution data, tail-end farmers in this section "
        "have received below-threshold allocations for the past 3 days. This constitutes a "
        "medium-priority equity violation. Recommended resolution: increase tail-end gate "
        "opening by 10% for the next 48 hours and verify delivery at field level."
    ),
    "dashboard_insight": (
        "Tail-end villages are receiving 18% less water than their expected allocation. "
        "The system recommends increasing their next irrigation window by 25 minutes and "
        "reducing head-reach window by 10 minutes to restore equity balance."
    ),
    "dispute_mediation": (
        "Analysis of water distribution records and sensor data confirms a systematic "
        "under-delivery to tail-end farmers. This appears to be a structural canal flow "
        "issue rather than deliberate interference. Recommended action: Field inspection "
        "of gates M3 and T1, technical adjustment of flow splitters, and a compensation "
        "allocation in the next irrigation cycle."
    ),
    "schedule_summary": (
        "Today's irrigation schedule has been optimised for water equity. Tail-end farmers "
        "receive a 12% allocation boost to compensate for historical deficit. All critical "
        "crop-stress cases have been prioritised. Human approval required for gate adjustments "
        "exceeding 15% change."
    ),
}


async def call_granite(prompt: str, context_type: str = "general") -> str:
    """
    Call IBM Granite LLM. Falls back gracefully if API key not configured.

    Parameters
    ----------
    prompt       : The full prompt to send to Granite
    context_type : Used to select fallback response category
    """
    model = _get_model()

    if model is None:
        # Offline / demo mode
        return FALLBACK_RESPONSES.get(context_type, _generic_fallback(prompt))

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_text(prompt=prompt)
        )
        return response.strip()
    except Exception as e:
        print(f"[Granite] Generation error: {e}")
        return FALLBACK_RESPONSES.get(context_type, _generic_fallback(prompt))


def _generic_fallback(prompt: str) -> str:
    if "water" in prompt.lower() or "allocation" in prompt.lower():
        return FALLBACK_RESPONSES["shortage_explanation"]
    if "complaint" in prompt.lower() or "dispute" in prompt.lower():
        return FALLBACK_RESPONSES["complaint_analysis"]
    return "AI analysis complete. Please review the dashboard for detailed metrics and recommendations."


# ─── Domain-specific Granite calls ───────────────────────────────────────────

SYSTEM_PROMPT = """You are Narmada Jal Nyay AI, an expert water management assistant for 
the Gujarat Narmada canal system. You help canal authorities and farmers with fair water 
distribution. Always be factual, concise, and farmer-friendly. Support both English and Gujarati.
Never make legally binding decisions. Always recommend human review for critical actions."""


async def explain_farmer_alert(farmer_name: str, village: str, reach_type: str,
                                allocated_m3: float, expected_m3: float,
                                slot_start: str, crop: str,
                                language: str = "en") -> str:
    lang_note = "Respond in Gujarati (Gujarat script)." if language == "gu" else "Respond in simple English."
    fairness = allocated_m3 / max(expected_m3, 1) * 100
    prompt = f"""{SYSTEM_PROMPT}

{lang_note}

Generate a friendly farmer notification for:
- Farmer: {farmer_name}, Village: {village} ({reach_type}-reach)
- Crop: {crop}
- Irrigation slot: {slot_start}
- Allocated water: {allocated_m3:.0f} cubic metres ({fairness:.0f}% of expected)

Keep it under 80 words. Mention the time to prepare the field."""
    return await call_granite(prompt, "farmer_alert")


async def explain_water_shortage(shortage_pct: float, affected_villages: list,
                                  head_eq: float, tail_eq: float) -> str:
    prompt = f"""{SYSTEM_PROMPT}

Explain the current canal water shortage situation to farmers:
- Shortage level: {shortage_pct*100:.1f}%
- Affected villages: {', '.join(affected_villages[:5])}
- Head-reach equity score: {head_eq:.0%}
- Tail-reach equity score: {tail_eq:.0%}
- Head-tail gap: {(head_eq - tail_eq)*100:.1f}%

Explain in 3-4 sentences. Be empathetic. Explain what the AI system is doing to help tail-end farmers."""
    return await call_granite(prompt, "shortage_explanation")


async def analyze_complaint(complaint_text: str, farmer_name: str,
                             village: str, reach_type: str,
                             allocation_history: str) -> Dict[str, str]:
    prompt = f"""{SYSTEM_PROMPT}

Analyze this farmer complaint and provide:
1. Summary (1 sentence)
2. Root cause (1-2 sentences)
3. Severity: normal/low/medium/high/critical
4. Recommendation for canal authority (2-3 sentences)

Farmer: {farmer_name}, {village} ({reach_type}-reach)
Complaint: "{complaint_text}"
Recent allocation history: {allocation_history}

Format your response as:
SUMMARY: ...
ROOT_CAUSE: ...
SEVERITY: ...
RECOMMENDATION: ..."""
    response = await call_granite(prompt, "complaint_analysis")
    return _parse_complaint_response(response, complaint_text)


def _parse_complaint_response(response: str, original: str) -> Dict[str, str]:
    lines = response.strip().split("\n")
    parsed = {
        "summary": "",
        "root_cause": "",
        "severity": "medium",
        "recommendation": "",
        "full_response": response,
    }
    for line in lines:
        if line.startswith("SUMMARY:"):
            parsed["summary"] = line.replace("SUMMARY:", "").strip()
        elif line.startswith("ROOT_CAUSE:"):
            parsed["root_cause"] = line.replace("ROOT_CAUSE:", "").strip()
        elif line.startswith("SEVERITY:"):
            sev = line.replace("SEVERITY:", "").strip().lower()
            parsed["severity"] = sev if sev in ["normal","low","medium","high","critical"] else "medium"
        elif line.startswith("RECOMMENDATION:"):
            parsed["recommendation"] = line.replace("RECOMMENDATION:", "").strip()

    # Fallbacks
    if not parsed["summary"]:
        parsed["summary"] = "Complaint regarding water allocation received."
    if not parsed["recommendation"]:
        parsed["recommendation"] = FALLBACK_RESPONSES["complaint_analysis"]

    return parsed


async def generate_dashboard_insight(schedule_summary: str, head_eq: float,
                                      tail_eq: float, shortage_pct: float,
                                      active_alerts: int) -> str:
    prompt = f"""{SYSTEM_PROMPT}

Generate a 2-3 sentence natural language insight for the canal authority dashboard:
- Schedule summary: {schedule_summary}
- Head equity: {head_eq:.0%}, Tail equity: {tail_eq:.0%}
- Shortage: {shortage_pct*100:.1f}%
- Active alerts: {active_alerts}

Be specific. Mention the head-tail gap. Recommend one concrete action."""
    return await call_granite(prompt, "dashboard_insight")


async def recommend_dispute_resolution(complaint_text: str, evidence_summary: str,
                                        head_tail_data: str) -> str:
    prompt = f"""{SYSTEM_PROMPT}

A dispute has been flagged. Recommend a fair resolution for the canal authority to review.
Important: This is a RECOMMENDATION only. Final decision requires human canal authority approval.

Complaint: {complaint_text}
Evidence: {evidence_summary}
Distribution data: {head_tail_data}

Provide a structured resolution recommendation in 3-5 sentences. 
Explicitly state this requires human approval."""
    return await call_granite(prompt, "dispute_mediation")


async def answer_chat_query(question: str, context_data: Dict[str, Any]) -> str:
    """General-purpose AI assistant for the farmer/authority chatbot."""
    ctx_str = "\n".join([f"{k}: {v}" for k, v in context_data.items()])
    prompt = f"""{SYSTEM_PROMPT}

Current system context:
{ctx_str}

User question: {question}

Answer clearly and helpfully in 2-4 sentences. If you don't have enough data, say so honestly."""
    return await call_granite(prompt, "general")
