"""
supabase_client.py
──────────────────
Supabase client for HumxnMed AI.
Handles auth, session persistence, health history, and user profiles.

Supabase SQL to run in your project dashboard:
─────────────────────────────────────────────

-- User health profiles
CREATE TABLE public.health_profiles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT,
  date_of_birth DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Health sessions (conversation history)
CREATE TABLE public.health_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  profile_id UUID REFERENCES public.health_profiles(id),
  raw_input TEXT NOT NULL,
  condition_identified TEXT,
  briefing JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Symptom logs
CREATE TABLE public.symptom_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symptom TEXT NOT NULL,
  severity INTEGER CHECK (severity BETWEEN 1 AND 10),
  notes TEXT,
  logged_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medication tracker
CREATE TABLE public.medications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  dosage TEXT,
  frequency TEXT,
  start_date DATE,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE public.health_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptom_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medications ENABLE ROW LEVEL SECURITY;

-- RLS policies: users only see their own data
CREATE POLICY "Users own their profiles" ON public.health_profiles FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own their sessions" ON public.health_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own their symptoms" ON public.symptom_logs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own their medications" ON public.medications FOR ALL USING (auth.uid() = user_id);
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_supabase: Optional[Client] = None


def get_supabase() -> Optional[Client]:
    """Get or create Supabase client. Returns None if not configured."""
    global _supabase
    if _supabase is not None:
        return _supabase

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        logger.warning("Supabase not configured — running without persistence")
        return None

    try:
        _supabase = create_client(url, key)
        logger.info("Supabase client initialized")
        return _supabase
    except Exception as e:
        logger.error(f"Supabase init failed: {e}")
        return None


def supabase_configured() -> bool:
    """True only when a real Supabase project is wired up (URL + key set). The `supabase`
    package being importable is NOT enough — accounts stay OFF until this is True, so the
    login UI never shows a signup that can't work."""
    return bool(os.getenv("SUPABASE_URL")) and bool(
        os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    )


# ── ENTITLEMENTS (which tier an email owns) ──────────────────────────────────
# The ONLY account data we store server-side: an email and which paid tier it owns.
# Health data never lives here — it stays on the device. This is what lets a purchase
# follow the customer across devices: they buy (Stripe records the tier for their email),
# then sign in with that email on any device and their tier unlocks.
#
# Run this SQL in the Supabase project (SQL Editor):
#   create table if not exists public.entitlements (
#     email text primary key,
#     tier text not null,
#     source text,
#     updated_at timestamptz default now()
#   );
#   alter table public.entitlements enable row level security;
#   -- The server uses the service key (bypasses RLS); no public policies needed.
def _norm_email(email: str) -> str:
    return (email or "").strip().lower()


async def add_to_waitlist(email: str, source: str = "") -> bool:
    """Store a crowdfunding/pre-launch 'notify me' email. Graceful: no-op if Supabase or the
    waitlist table isn't set up. SQL:
      create table if not exists public.waitlist (
        email text primary key, source text, created_at timestamptz default now());
      alter table public.waitlist enable row level security;"""
    sb = get_supabase()
    e = _norm_email(email)
    if not sb or not e:
        return False
    try:
        from datetime import datetime, timezone
        sb.table("waitlist").upsert(
            {"email": e, "source": source, "created_at": datetime.now(timezone.utc).isoformat()},
            on_conflict="email",
        ).execute()
        return True
    except Exception as ex:
        logger.error(f"waitlist error: {ex}")
        return False


async def get_entitlement(email: str) -> Optional[str]:
    """Return the tier an email owns (e.g. 'clinical'), or None."""
    sb = get_supabase()
    e = _norm_email(email)
    if not sb or not e:
        return None
    try:
        r = sb.table("entitlements").select("tier").eq("email", e).limit(1).execute()
        rows = r.data or []
        return rows[0]["tier"] if rows else None
    except Exception as ex:
        logger.error(f"get_entitlement error: {ex}")
        return None


async def set_entitlement(email: str, tier: str, source: str = "") -> bool:
    """Record that an email owns a tier (upsert). Called after a verified purchase."""
    sb = get_supabase()
    e = _norm_email(email)
    if not sb or not e or not tier:
        return False
    try:
        from datetime import datetime, timezone
        sb.table("entitlements").upsert(
            {"email": e, "tier": tier, "source": source,
             "updated_at": datetime.now(timezone.utc).isoformat()},
            on_conflict="email",
        ).execute()
        return True
    except Exception as ex:
        logger.error(f"set_entitlement error: {ex}")
        return False


async def save_session(
    user_id: str,
    raw_input: str,
    condition: str,
    briefing: dict,
) -> Optional[str]:
    """Save a completed health session to Supabase."""
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("health_sessions").insert({
            "user_id": user_id,
            "raw_input": raw_input,
            "condition_identified": condition,
            "briefing": briefing,
        }).execute()
        return result.data[0]["id"] if result.data else None
    except Exception as e:
        logger.error(f"save_session error: {e}")
        return None


async def get_user_history(user_id: str, limit: int = 20) -> list:
    """Fetch a user's health session history."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        result = sb.table("health_sessions") \
            .select("id, raw_input, condition_identified, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_user_history error: {e}")
        return []


async def log_symptom(user_id: str, symptom: str, severity: int, notes: str = "") -> bool:
    """Log a symptom entry."""
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("symptom_logs").insert({
            "user_id": user_id,
            "symptom": symptom,
            "severity": severity,
            "notes": notes,
        }).execute()
        return True
    except Exception as e:
        logger.error(f"log_symptom error: {e}")
        return False


async def get_symptom_history(user_id: str, limit: int = 50) -> list:
    """Get a user's symptom history for pattern detection."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        result = sb.table("symptom_logs") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("logged_at", desc=True) \
            .limit(limit) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_symptom_history error: {e}")
        return []


# ── PHYSICIAN REVIEW (Reviewed by a Real Doctor) ─────────────────────────────
# Run this SQL in Supabase (also in store/DOCTOR_PORTAL.md):
#   create table public.physician_reviews (
#     id uuid default gen_random_uuid() primary key,
#     raw_input text, condition text, briefing jsonb,
#     status text default 'pending',
#     doctor_name text, verdict text, note text,
#     created_at timestamptz default now(), reviewed_at timestamptz
#   );
#   alter table public.physician_reviews enable row level security;
#   -- the server uses the service key (bypasses RLS); no public policies needed.
async def request_review(raw_input: str, condition: str, briefing: dict) -> Optional[dict]:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("physician_reviews").insert({
            "raw_input": raw_input, "condition": condition, "briefing": briefing, "status": "pending",
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"request_review error: {e}")
        return None


async def get_review(review_id: str) -> Optional[dict]:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("physician_reviews") \
            .select("id, status, doctor_name, verdict, note, reviewed_at") \
            .eq("id", review_id).limit(1).execute()
        return (result.data or [None])[0]
    except Exception as e:
        logger.error(f"get_review error: {e}")
        return None


async def get_pending_reviews(limit: int = 50) -> list:
    sb = get_supabase()
    if not sb:
        return []
    try:
        result = sb.table("physician_reviews") \
            .select("id, raw_input, condition, briefing, created_at") \
            .eq("status", "pending").order("created_at").limit(limit).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_pending_reviews error: {e}")
        return []


async def export_user_data(user_id: str) -> dict:
    """HIPAA patient right: return everything we store about this user."""
    sb = get_supabase()
    if not sb:
        return {}
    out = {}
    for tbl, col in (("health_profiles", "user_id"), ("health_sessions", "user_id"), ("symptom_logs", "user_id"), ("medications", "user_id")):
        try:
            r = sb.table(tbl).select("*").eq(col, user_id).execute()
            out[tbl] = r.data or []
        except Exception as e:
            logger.error(f"export {tbl} error: {e}")
            out[tbl] = []
    return out


async def delete_user_data(user_id: str) -> bool:
    """HIPAA patient right: delete all of this user's data, and the auth account."""
    sb = get_supabase()
    if not sb:
        return False
    ok = True
    for tbl in ("symptom_logs", "medications", "health_sessions", "health_profiles"):
        try:
            sb.table(tbl).delete().eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"delete {tbl} error: {e}")
            ok = False
    try:
        sb.auth.admin.delete_user(user_id)
    except Exception as e:
        logger.error(f"delete auth user error: {e}")
    return ok


async def clear_user_data(user_id: str) -> bool:
    """Patient right: delete all of this user's health data WITHOUT deleting the account."""
    sb = get_supabase()
    if not sb:
        return False
    ok = True
    for tbl in ("symptom_logs", "medications", "health_sessions", "health_profiles"):
        try:
            sb.table(tbl).delete().eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"clear {tbl} error: {e}")
            ok = False
    return ok


async def delete_symptom_entry(user_id: str, entry_id: str) -> bool:
    """Delete a single symptom log entry, scoped to its owner."""
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("symptom_logs").delete().eq("id", entry_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        logger.error(f"delete_symptom_entry error: {e}")
        return False


async def sign_review(review_id: str, doctor_name: str, verdict: str, note: str = "") -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        from datetime import datetime, timezone
        sb.table("physician_reviews").update({
            "status": "reviewed", "doctor_name": doctor_name, "verdict": verdict,
            "note": note, "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", review_id).execute()
        return True
    except Exception as e:
        logger.error(f"sign_review error: {e}")
        return False
