"""guardrail_node.py - Node 1

Safety classifier. This node decides whether a patient's words get routed to 911
guidance, 988 crisis resources, or the normal briefing pipeline.

DESIGN RULE: this node fails CLOSED. If the classifier cannot produce a status we
recognise -- API error, timeout, unparseable output, unknown category -- the result
is `unavailable`, which terminates the graph with a safe message. It must never
degrade to `pass`, because `pass` sends someone in crisis into symptom extraction
instead of to 988.
"""
import json, logging, re
import anthropic
from ..state import PatientState

logger = logging.getLogger(__name__)
client = None

def get_client():
    global client
    if client is None:
        client = anthropic.Anthropic()
    return client

try:
    from langsmith import traceable
except ImportError:
    def traceable(**kw):
        def decorator(fn): return fn
        return decorator

# The only statuses the router knows how to handle. Anything else fails closed.
VALID_STATUSES = ("pass", "emergency", "crisis", "off_topic", "invalid")

# Deterministic backstop, used ONLY when the classifier is unreachable (see the
# except branch). High-precision phrases only. It can only ever ADD safety routing
# -- it is never consulted on the success path, so it cannot override the model or
# introduce false positives into normal operation.
_CRISIS_RE = re.compile(
    r"\b(kill(ing)? myself|end(ing)? my life|take my own life|want(ing)? to die|"
    r"wanna die|suicidal|suicide|hurt myself|harm myself|self[- ]harm|"
    r"no reason to live|better off dead)\b", re.I)
_EMERGENCY_RE = re.compile(
    r"\b(chest pain|can'?t breathe|cannot breathe|trouble breathing|not breathing|"
    r"heart attack|stroke|unconscious|unresponsive|severe bleeding|bleeding badly|"
    r"overdose|anaphyla\w*)\b", re.I)

def _local_prescreen(text: str):
    """Crisis > emergency, matching the model's own precedence. None = no match."""
    if not text:
        return None
    if _CRISIS_RE.search(text):
        return "crisis"
    if _EMERGENCY_RE.search(text):
        return "emergency"
    return None

def _first_text(resp) -> str:
    """First text block. Never index content[0] blindly -- a refusal returns an
    empty content list, and thinking-enabled models put a thinking block first."""
    for block in (getattr(resp, "content", None) or []):
        if getattr(block, "type", None) == "text":
            return block.text or ""
    return ""

def _parse_status(text: str):
    """Pull a status out of the model's reply. Tolerates markdown fences, which
    models routinely add and which json.loads() chokes on. Returns (status, message)
    or (None, "") when nothing valid could be read."""
    if not text:
        return None, ""
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```(?:json)?\s*", "", body)
        body = re.sub(r"\s*```$", "", body).strip()
    if not body.startswith("{"):
        m = re.search(r"\{.*\}", body, re.S)  # JSON embedded in prose
        body = m.group(0) if m else body
    try:
        result = json.loads(body)
    except (ValueError, TypeError):
        return None, ""
    if not isinstance(result, dict):
        return None, ""
    status = str(result.get("status") or "").strip().lower()
    if status not in VALID_STATUSES:
        return None, ""
    message = result.get("message") or ""
    return status, (message if isinstance(message, str) else "")

SYSTEM = """You are a safety classifier for a patient health information tool.
Classify the input into exactly one category:
- pass: health-related question appropriate to answer
- emergency: life-threatening symptoms requiring immediate 911 response
- crisis: mental health crisis or suicidal ideation requiring 988 referral
- off_topic: completely unrelated to health
- invalid: gibberish or too vague
Respond ONLY with valid JSON: {"status": "<category>", "message": "<warm human message if blocked, else empty string>"}"""

@traceable(name="guardrail_node", tags=["safety"])
def guardrail_node(state: PatientState) -> dict:
    raw = state.get("raw_input", "").strip()
    has_image = bool(state.get("image_data"))
    # An attached photo (lab result / document) IS the content — so empty or thin
    # text is fine when an image is present. Only reject truly-empty requests.
    if not raw and not has_image:
        return {"guardrail_status": "invalid", "guardrail_message": "Please share what's on your mind.", "current_node": "guardrail"}
    # Medication-interaction mode: a bare list of meds/foods is a valid health
    # question here, so tell the classifier not to treat it as "too vague".
    system = SYSTEM
    user_content = raw or "Please explain the attached image."
    if (state.get("intent") or "").lower() in ("medication", "pharmacist"):
        system = SYSTEM + (
            "\n\nCONTEXT: The user is using a medication-interaction checker. "
            "A list of medications, foods, or drinks (even without a full sentence) "
            "is a valid health question — classify it as 'pass' unless it is an "
            "emergency, crisis, gibberish, or clearly unrelated to health."
        )
        user_content = f"Medication/interaction check: {raw}"
    if has_image:
        system = system + (
            "\n\nCONTEXT: The user has ATTACHED AN IMAGE (a photo of a lab result, "
            "prescription, or medical document) along with their text. The image IS "
            "the content to explain, so brief or vague text such as 'explain this' or "
            "'what does this mean' is a valid 'pass' — do NOT classify it as invalid "
            "or off_topic just because the text is short. Only use emergency or crisis "
            "for a genuine safety issue in the text."
        )
    try:
        resp = get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user_content}]
        )
        status, message = _parse_status(_first_text(resp))
        if status is None:
            # Reply was unreadable or named a category we don't route. Treat exactly
            # like an outage rather than guessing — see the except branch.
            raise ValueError("guardrail returned no usable status")
        # Safety net: never let an attached image get bounced as vague/unrelated.
        # Emergency/crisis still take priority (real safety), but invalid/off_topic
        # on an image-bearing request becomes a pass so the photo gets analyzed.
        if has_image and status in ("invalid", "off_topic"):
            status = "pass"
        message = "" if status == "pass" else message
        return {"guardrail_status": status, "guardrail_message": message, "current_node": "guardrail", "error": None}
    except Exception as e:
        # FAIL CLOSED. We could not classify, so we do not know this is safe to answer.
        logger.error(f"guardrail_node unavailable, failing closed: {e}", exc_info=True)
        fallback = _local_prescreen(raw)
        if fallback:
            logger.warning(f"guardrail local prescreen matched '{fallback}' while classifier was down")
            return {"guardrail_status": fallback, "guardrail_message": "", "current_node": "guardrail", "error": None}
        return {"guardrail_status": "unavailable", "guardrail_message": "", "current_node": "guardrail", "error": None}
