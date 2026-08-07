# HumxnMed — HIPAA Readiness Plan (the real path)
### Updated 2026-08-06. Launch model: **consumer now + clinical "de-identified only" until compliant.**

**The honest frame:** HIPAA compliance is a *legal + operational state*, not a code feature. It needs
(1) signed BAAs, (2) a HIPAA-eligible host, (3) a security program. Code makes you *ready*; it can't make
you *compliant*. **Do not claim HIPAA anywhere until all three are true.**

---

## Where you are RIGHT NOW (safe + honest)
- **Consumer app**: does NOT require HIPAA (a person using the app on their own data isn't covered). Launch it.
- **Clinician tools**: usable now **for de-identified data only** — the console explicitly tells clinicians not
  to enter full names/MRNs until BAAs are in place. This is the honest interim; no false claim.
- **Technical readiness already built:** no PHI in logs · content not stored by default · rate limits + auth ·
  security headers · and a **`MC_BAA_ONLY`** switch that routes patient voice only through a BAA-capable vendor.

## Step 1 — Sign BAAs (you; ~days–2 weeks)
Request a BAA from each vendor that touches patient data. Template email:

> *Subject: BAA request — [Vendor] for HumxnMed (Millennials Creatives LLC)*
> *We use [Vendor] to process health information in our application and need to execute a Business
> Associate Agreement (HIPAA), plus confirm zero-/limited-data-retention for our API traffic. Please send
> your BAA and the steps to enable a HIPAA-eligible configuration on our account. — [name], Millennials Creatives LLC*

| Vendor | Used for | BAA? | Action |
|---|---|---|---|
| **Anthropic** | text AI (core) | ✅ offers | Request BAA; enable zero-retention |
| **OpenAI** | voice STT/TTS | ✅ offers | Request BAA + zero-retention (Enterprise/API) |
| **Groq** | voice STT | ❌ likely no | **Drop for PHI** — set `MC_BAA_ONLY=1` (uses OpenAI instead) |
| **ElevenLabs** | read-aloud | ⚠️ check enterprise | If no BAA, `MC_BAA_ONLY=1` uses OpenAI TTS |
| **Supabase** | accounts (email+tier) | ✅ paid (Team) | Only if you store PHI there (you don't today) |
| **Stripe** | payments | N/A (not PHI) | No BAA needed; never send health data to it |
| **Your host** | everything | see Step 2 | The blocker — Railway won't sign |

## Step 2 — Move to a HIPAA-eligible host (the real work; ~days–2 weeks)
**Railway does not sign BAAs**, so the clinical/PHI traffic must run somewhere that will. Options:
- **Aptible** — HIPAA PaaS, signs BAA, closest to Railway's feel. Easiest lift.
- **Render (paid HIPAA)** / **Fly.io** (BAA available) — also PaaS-like.
- **Google Cloud Run / AWS** (BAA via the cloud provider) — most control, more setup.
I can prepare the migration (Dockerfile/config are portable); you create the account + sign the BAA.

## Step 3 — Stand up the security program (~2–6 weeks to "ready")
- Use **Vanta** or **Drata** (~$10–30k/yr) to run: risk assessment, policies, workforce training, access
  controls, audit logging, breach procedures. They also drive **SOC 2** when you sell to larger orgs.
- A healthcare attorney reviews your BAAs-in, Notice of Privacy Practices, and the clinical terms.

## Step 4 — Flip it on (me + you)
Once BAAs signed + on the new host:
1. Set `MC_BAA_ONLY=1` (voice → OpenAI only).
2. Move any stored-PHI features onto the compliant host/DB.
3. I turn on PHI-access audit logging and remove the "de-identified only" clinical banner.
4. **Only then** may the product say it supports PHI under HIPAA — with the BAAs on file.

## Timeline (realistic)
- **Today:** consumer launches; clinical = de-identified only. ✅
- **~2 weeks:** BAAs signed + host migrated → full clinical PHI, HIPAA-ready.
- **~1–3 months:** SOC 2 Type II (only needed to sell to hospitals/big orgs).

## Do NOT do
- Do not put "HIPAA compliant" on the site, the Kickstarter, or in sales until Steps 1–3 are done.
- Do not let clinicians enter identifiable PHI until then (the console already warns them).
