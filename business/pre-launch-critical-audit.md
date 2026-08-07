# HumxnMed — Pre-Launch Critical Audit
### "What the journalist writes first" — a hostile, code-cited review (2026-08-06)

Six independent adversarial reviewers (privacy, medical/regulatory, security, accessibility,
architecture/platform, UX) read the live site and the actual source. This is the ammunition a
skeptical tech reporter, a regulator, or a security researcher would use. Findings are ranked by
**how badly they'd hurt in print**, deduped across reviewers, with the file/behavior that proves them.

> **The one-paragraph story a reporter would open with:**
> *"HumxnMed markets itself as the private, local-first, 'nothing leaves your phone' health app that
> 'never sells your data' — while its own code streams patients' symptoms, uploaded lab photos and
> recorded voices to at least five outside AI vendors it admits it has no HIPAA agreements with,
> logs your diagnosis to the server, and exposes an endpoint that lets anyone download or delete any
> patient's records by changing an ID in the URL. It brands itself 'not a diagnosis, not a medical
> device' while its code returns a 'most likely condition,' an 'emergency now' triage level, and
> reads your X-rays — and it's raising money on Kickstarter."*

---

## TIER 1 — Kickstarter-killers (any one of these is a headline)

### 1. The core privacy promise is contradicted by the company's own code
- "We store nothing by default / your health content is not written to our database" (trust.html) — but
  `/user/symptoms/log` and `/review/request` write verbatim symptoms, severity, notes and raw health
  descriptions to Supabase **with no flag check** (`supabase_client.py`, `server.py`). `MC_STORE_HISTORY`
  only guards one path.
- `logger.info(f"confirm: final_condition=...")` writes the **identified condition** to server logs, three
  lines under a hardcoded `"we_never_log_your_health_content": True`.
- **Journalist:** *"'We never log your health content' isn't something HumxnMed verifies — it's a `True`
  typed into the source, right above the line that logs your diagnosis."*

### 2. PHI goes to 5+ third parties with NO BAA — while selling a "Clinical" tier to practices
- Health text → Anthropic; audio → Groq/OpenAI/ElevenLabs; pipeline traces → **LangSmith** (undisclosed);
  accounts/reviews → Supabase; analytics → **PostHog** (undisclosed, session-replay capable). trust.html
  admits BAAs/HIPAA/SOC2 are "in progress" (= none). clinical.html is onboarding paid pilot practices at $39.
- **Journalist:** *"A clinician dictating a note into HumxnMed's 'point-of-care console' ships that patient's
  identifiable data to four AI companies the app admits it has no HIPAA agreement with."*

### 3. Unauthenticated IDOR: anyone can export or delete any patient's records
- `GET /user/{id}/export|history|symptoms` and `POST /user/delete` have **no auth, no ownership check**; the
  Supabase client uses the **service-role key**, so the documented Row-Level-Security policies never run.
- **Journalist:** *"A medical app let anyone download or erase any patient's health records by changing a
  number in the URL."*

### 4. "Not a diagnosis / not a medical device" is contradicted by the code — and they knew the line
- `normalization_v2.py` returns `primary_condition` + `urgency: emergency_now|see_doctor_today`; the triage
  UI renders "CALL 911 / GO TO THE ER"; `vision_node.py` flags lab values `high/low` and classifies skin/X-ray
  images; a live patient-facing button asks the AI for drug–drug interactions. FDA's Jan 2026 CDS guidance:
  patient-facing decision support = a device. `/clinical-weigh`'s docstring even cites the exemption statute,
  then fails its "independently review the basis" requirement (the "basis" is model-generated text).
- **Journalist:** *"They wrote FDA's exemption into a code comment, then shipped the exact feature it
  excludes — and gave patients a 'most likely condition' and an 'emergency now' alarm the whole app swears
  it doesn't produce."*

### 5. Machine-translated, unreviewed safety copy — including the 988 suicide line
- `mc-i18n.js` claims disclaimers/safety text are never machine-translated (marked `.mc-authoritative`) — but
  **zero** pages use that marker on safety copy. The 988 crisis line, "not an emergency service" disclaimer,
  and printed handout red-flags ("get help right away if…") are AI-translated into 14 languages with no human
  review. A flipped negation in a translated red flag is a patient-harm event.
- **Journalist:** *"On the app that promises 'no one gets left out,' the suicide-hotline instructions are
  handed to an AI translator with nobody checking the result."*

### 6. The iOS app is a web-wrapper pinned to a dead-branded URL
- `capacitor.config.json` `server.url = https://medcompanion-ai.up.railway.app` (the OLD name), `cleartext:true`.
  Apple rejection risk (Guideline 4.2 "repackaged website" + 2.5.2 remote code), and any host change **bricks
  every installed app**. Store listing still says "MedCompanion AI."
- **Journalist:** *"HumxnMed's 'app' is a browser in a trench coat, hard-coded to a Railway URL bearing the
  company's abandoned name — change the address and every phone shows a white screen."*

### 7. Fake scarcity pricing over a 100%-free app
- `MC_GATING` defaults OFF; the paywall, trial timer, and founder unlock **do nothing**. Yet /founding sells
  "lock in your founding price forever — only the first 500," and pushes Plus/Pro/Clinical.
- **Journalist:** *"HumxnMed dangles 'only 500 founding spots, lock in forever' over a product where every
  feature is already free and the paywall is switched off."*

---

## TECH-SIDE CRITICISMS

### Privacy / claims-vs-reality
- Undisclosed **LangSmith** tracing of the full health pipeline (server.py:7-9). Undisclosed **PostHog**
  session-replay tracker in `/app` (index.html) vs "never tied to a profile."
- i18n `MutationObserver` re-sends the AI's medical answer **and echoed user input** to Anthropic for
  non-English users.
- "Audio not retained by HumxnMed" is a dodge — the raw voice is uploaded to Groq/OpenAI/ElevenLabs (their
  retention, no BAA).
- privacy.html (old brand, `team@medcompanionai.com`) never mentions voice, image upload, Epic/FHIR import,
  Supabase, or clinician use — materially under-discloses.
- "Never train on your data. Full stop." — a promise made on behalf of vendors not yet contractually bound.

### Security
- **No auth/authorization on essentially any endpoint**; service-role key = RLS never enforced.
- **Client-side-only paywall** (`localStorage.mc_tier`) — `localStorage.setItem('mc_tier','clinical')` unlocks
  everything; AI endpoints check no token/tier.
- **Unauthenticated LLM/voice endpoints + no rate limiting + no size caps** = uncapped financial DoS on the
  owner's AI bills (`/transcribe`, `/i18n-batch`, `/speak`, `/session/start`…). Wildcard CORS lets any site
  drive it from a victim's browser.
- Founder codes **hardcoded in source** (`FOUNDINGRN,FOUNDER2026`); `/redeem-code` unthrottled.
- `/admin/grant` and doctor-key use **non-constant-time** `!=` compare; no throttle. OTP verify has no
  app-level brute-force lockout. Physician-review queue leaks all patients' PHI behind one shared static key.
- `/verify-purchase` treats `no_payment_required` as paid (100%-off coupon → free Clinical) and leaks buyer email.
- **Done right:** output escaped via `clean()` (XSS largely mitigated); no secrets committed except founder
  codes; path traversal defended; no account enumeration on request-code; Stripe verified server-side.

### Medical / regulatory / safety
- Consumer briefing **citations can be AI-fabricated** (briefing_node fallback emits model-authored source
  URLs) while the app advertises "every briefing cites NIH/Mayo/FDA, real live links."
- Gated allergy checker is **theater** — the conservative curated check is disabled "for FDA," the unbounded
  generative interaction check is live. And the curated map misses penicillin↔cephalosporin cross-reactivity.
- Scribe writes into the **legal medical record** with "you review it" as the only guardrail (automation bias).
- Internal disclaimer contradictions: "not an emergency service" + "CALL 911"; "no dosing" + `how_taken`
  dosing; "not for time-critical decisions" + marketed "for the OR, the Pit, on rounds."
- Planned **CPT/E&M code suggestions** to clinicians = False Claims Act / upcoding exposure.
- **Done right:** RxNorm/LOINC/ICD-10 mappings are real and deterministic (NIH), not model-generated
  (SNOMED is gated/overstated); clinician side is honest about "BAA in progress."

### Architecture / performance / platform
- **Single-process server blocks its own event loop**: ~19 AI endpoints call the synchronous Anthropic SDK
  inside `async def` (only the final briefing is offloaded). Effective concurrency ≈ 1 AI request at a time.
- **All state in RAM**: LangGraph `MemorySaver`, briefing jobs, i18n cache — lost on every redeploy; can't
  scale horizontally. ("Postgres checkpointer" is only a docstring.)
- Single Railway **nano**, no CDN for a **556 KB / 8,090-line** unminified `index.html` (351 inline onclicks,
  no build step); `restartPolicyMaxRetries:3` then it stays down; no healthcheck.
- **Single AI vendor** (Anthropic) for the whole text pipeline — one rate-limit = total outage.
- First non-English visit fires **dozens of blocking LLM translation calls**, re-bought after each deploy.
- **No tests** anywhere; every failure swallowed into "please try again." Two service workers fight; the page
  unregisters all SWs then re-registers every load.
- Rebrand half-done: bundle id, store name, Epic OAuth redirect all still "medcompanion."

### Accessibility & i18n (extra sting given "no one gets left out")
- The core **symptom/compose boxes have no labels** (placeholder-only) — invisible to screen readers.
- **~35 clickable `<div>/<span>`** with no keyboard access; ~28 modals with **no focus trap/return** (incl. the
  crisis dialog).
- Dark-theme green buttons **~2.2:1 contrast** (fail); gold pills ~2.5:1.
- **RTL is a global flag** on a layout full of hardcoded `left/right` px — Arabic/Farsi render mirrored/broken.
- Flash-of-English + screen reader announces wrong language while English text loads; AI streamed into a
  `aria-live` region floods screen readers; broken heading outline (two `<h1>`, no `<h3>`).
- MT notice + "back to English" control are ~12–16px, below tap-target minimums.

---

## USER-SIDE CRITICISMS

- **"Ten products, one logo."** Symptom-explainer + med tracker + Health Passport + encrypted vault + estate/
  affairs organizer + family hub + clinician console + scribe + handout generator + attorney chronology.
  No one can say what it *is* in a sentence.
- **`/pro` collision:** the URL serves a **legal chronology tool for attorneys**, but "Pro" is also the $24.99
  consumer tier. People land on the wrong, off-brand product.
- **13-persona role gate** before you can type a symptom; defensive homepage ("I'm not a doctor, not ChatGPT,
  not WebMD") opens on three denials over a suicide-hotline banner.
- **Four competing clinician hubs** (/clinical, /console, /workspace, /pro) with no canonical front door; tool
  count says 4 on one page, 7–8 on another.
- **Schrödinger sign-in**: whether "Sign in" works depends on an invisible Supabase probe; historically a dead
  end + localhost email bug.
- **/redeem promises cross-device unlock** but stores it in localStorage (per-browser, wiped on cache clear).
- **Palette chaos**: 6+ greens for primary buttons; 3 golds — reads stitched-together/amateur.
- Orphan `/welcome` purchase-success page for purchases that can't happen; unverifiable "team of licensed
  clinicians" with no names; estate/will organizer two clicks from "my stomach hurts."

---

## PRIORITY FIX ORDER (before any public launch)

**Must-fix (legal/safety/trust — the headline risks):**
1. Make privacy claims literally true: stop ungated PHI writes, remove condition from logs, disclose or remove
   LangSmith + PostHog, rewrite privacy.html to list every data flow/vendor, stop claiming "on your device"
   for cloud features. Or narrow the claims to what's true.
2. Real auth + ownership on `/user/*`, `/session/*`, `/review/*`; stop using the service key as default DB
   identity (use the user JWT so RLS runs). Token + server-side entitlement on every AI endpoint; rate limits +
   size caps; constant-time secret compares; remove hardcoded founder codes; add CSP/security headers.
3. Resolve the device line: either pull patient-facing diagnosis/triage/vision-flagging/interaction features
   or accept the SaMD/FDA path. Don't cite the exemption in code while failing it.
4. Protect all crisis/safety/legal copy from machine translation (mark authoritative or professionally
   translate); no unreviewed MT on printed handout red-flags.
5. Fix the Kickstarter-optics contradiction: turn gating on and mean it, or drop the "500 founding spots /
   lock in forever" scarcity and say "free during beta."

**Should-fix (platform/credibility):**
6. Point `server.url` at the canonical domain; plan the Apple 4.2 story (or the app is a rejection/brick risk).
7. Offload blocking AI calls (`asyncio.to_thread`) + workers; move session/cache state out of RAM; add a CDN
   in front of the HTML; raise restart retries + healthcheck — or the launch spike browns out.
8. Accessibility baseline: label every input, make clickable divs real buttons, focus-trap modals, fix
   contrast, gate `dir=rtl` behind real RTL work.

**Product (the real cure):**
9. **Pick one audience and one sentence.** The patient "your health, finally explained" story is the
   strongest and most defensible; demote clinician + legal tools to a separate product/URL. Kill the persona
   gate, the orphan pages, and five of the six greens. Focus dissolves half the findings above.
