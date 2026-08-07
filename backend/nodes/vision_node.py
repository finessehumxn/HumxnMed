"""
vision_node.py — Optional Node
LangSmith traced image analysis for lab results, prescriptions, rashes.
Activated when the user uploads an image alongside their text input.
"""
import json
import base64
import logging
from langsmith import traceable
import anthropic
from ..state import PatientState

logger = logging.getLogger(__name__)
client = None

def get_client():
    global client
    if client is None:
        client = anthropic.Anthropic()
    return client

SYSTEM = """You are helping a patient READ a health document they uploaded — transcribing and
explaining what is printed on it in plain language. You are NOT interpreting, diagnosing, or making
a medical judgment. For anything that looks like a scan/X-ray or a skin photo, DO NOT attempt to
read or interpret it — say it needs a clinician to interpret and set flags to "unknown".

Respond ONLY with valid JSON:
{
  "image_type": "lab_results|prescription|skin_condition|medication|xray|other",
  "findings": "plain-language description of WHAT IS PRINTED on the document (transcription + what each item generally measures) — never a judgment about the person's health",
  "key_values": [
    {"name": "item name", "value": "value shown", "flag": "normal|low|high|unknown — set ONLY by comparing the value to the reference range PRINTED ON THE SAME DOCUMENT; if the document shows no reference range, or this is an image (xray/skin), use 'unknown'. This is a mechanical read of the paper, not a medical opinion."}
  ],
  "plain_summary": "2-3 sentences on what this document generally shows/measures in everyday language — not a conclusion about the person",
  "important_notes": "general things people often ask their doctor about for this kind of document",
  "disclaimer": "This only reads what's printed on your document — it is not a diagnosis or interpretation. Your doctor reads results in the context of your full health."
}

If the image is not health-related, return: {"image_type": "not_medical", "findings": "This does not appear to be a medical image.", "key_values": [], "plain_summary": "", "important_notes": "", "disclaimer": ""}"""


@traceable(name="vision_node", tags=["vision", "multimodal", "pipeline"])
def vision_node(state: PatientState) -> dict:
    """Process an uploaded medical image using Claude Vision."""
    image_data = state.get("image_data")
    image_media_type = state.get("image_media_type", "image/jpeg")

    if not image_data:
        return {"image_analysis": None, "current_node": "vision"}

    logger.info(f"vision_node analyzing {image_media_type} image")

    try:
        resp = get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": image_data,
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Please analyze this medical image. The patient also said: {state.get('raw_input', 'No additional context provided.')}"
                    }
                ]
            }]
        )
        # Never index content[0] blindly: a refusal returns an empty content list and
        # thinking-enabled models put a thinking block first. Find the text block.
        text = ""
        for _blk in (getattr(resp, "content", None) or []):
            if getattr(_blk, "type", None) == "text":
                text = _blk.text or ""
                break
        text = text.strip().replace("```json", "").replace("```", "")
        if "{" not in text or "}" not in text:
            raise ValueError("vision model returned no JSON object")
        analysis = json.loads(text[text.find("{"):text.rfind("}")+1])
        logger.info(f"vision_node completed: type={analysis.get('image_type')}")
        return {"image_analysis": analysis, "current_node": "vision", "error": None}
    except Exception as e:
        logger.error(f"vision_node error: {e}")
        return {"image_analysis": None, "current_node": "vision", "error": f"Image analysis failed: {e}"}



