# HumxnMed — Kickstarter Launch-Readiness Checklist
### Updated 2026-08-06. Sequenced so you can work top-to-bottom.

Everything in **§A is done** (code, live). **§B is you** (decisions/accounts/legal I can't do). **§C** is the
app rebuild. **§D** is the recommended order.

---

## §A — DONE and live (no action needed)
- ✅ **Security**: closed the record export/delete IDOR; auth+ownership on `/user/*`; rate-limiting + input caps
  on AI/voice endpoints; constant-time secret checks; restricted CORS; security headers.
- ✅ **Privacy truth**: removed the PostHog tracker; stopped logging the diagnosis; LangSmith off by default;
  gated the ungated PHI write; honest data-flow disclosure in `/privacy`.
- ✅ **Safety**: 988/911/emergency/"not a diagnosis" copy can never be machine-translated.
- ✅ **Claims**: removed the fake "500 spots / lock in forever" scarcity → honest "free during beta."
- ✅ **Accessibility**: keyboard operability for clickable elements, focus-trap + focus-return on all dialogs,
  input labels, button contrast, RTL stylesheet for Arabic/Farsi.
- ✅ **Scale**: all 20 blocking AI calls + the main patient-briefing run off the event loop (one slow request
  can't freeze the server); edge-cache headers so a CDN can absorb a spike.
- ✅ **FDA reframe (partial)**: outputs framed as *educational possibilities to discuss*, not determinations;
  vision reads only what's printed on the document; the patient AI drug-interaction check is gated off.
- ✅ **Accounts**: passwordless email-code sign-in is LIVE (Supabase connected).
- ✅ **App download**: App Store + Google Play badges on `/`, `/humxnmed`, `/clinical`.
- ✅ **Guide**: step-by-step `/guide` for patients and clinicians.

---

## §B — YOU must do before (or around) launch

### B1. Regulatory opinion — the #1 risk *(do first)*
- Hire a **digital-health / FDA regulatory attorney** (not a general lawyer) for a **scoping opinion** (~$3–10k).
- Show them: the symptom-explainer's `primary_condition` + `urgency` outputs, and the image-reading feature.
- Ask: *"With the educational reframing in place, does this stay a non-device, and is the wording sufficient?"*
- Outcome → either they bless it (launch), or they name specific changes (I implement them).

### B2. Legal pages review
- Have the attorney review **`/privacy`** and **`/terms`** (drafts) and your medical disclaimer.
- Update the contact email if you move off `team@medcompanionai.com`.

### B3. HIPAA — only if you market to clinicians/practices at launch
- **Consumer launch does NOT need HIPAA** (patient using their own data). If the Kickstarter is consumer-first,
  you can defer this.
- If clinicians will enter real patient data: request **BAAs** from Anthropic + OpenAI (they offer them), drop
  any vendor that won't sign (check Groq), consider a HIPAA-eligible host, and stand up a program with
  **Vanta/Drata** (~$10–30k/yr). Until then, the console tells clinicians to avoid identifying details.

### B4. Trademark
- File **HumxnMed** (classes 9 / 42 / 44, owner Millennials Creatives LLC) — your live app is your specimen.
  Clear the "Human Med AG" flag with the attorney first.

### B5. Store listings (rebrand) — see §C
- Update the App Store / Play **name** from "MedCompanion AI" → "HumxnMed" and refresh screenshots/icon.

### B6. Stripe (only if charging at launch)
- Turn on **receipt emails** (Settings → Customer emails → Successful payments).
- Set each payment link's after-payment redirect to `/welcome`.
- Decide: keep everything free during beta (recommended — matches the site) or turn gating on.

### B7. CDN (optional but recommended for a spike)
- Put **Cloudflare (free)** in front of `humxnmed.millennialscreatives.com` (proxy the DNS). The cache headers
  are already set server-side; Cloudflare will honor them and absorb repeat traffic.

---

## §C — The app rebuild (Codemagic — you run it)
**Your web fixes are ALREADY live inside installed apps** (the app loads the site remotely). A rebuild is only
needed to apply:
- the **HumxnMed name + new icon** (currently the store still shows "MedCompanion AI"),
- the updated **`server.url`** (now the canonical domain) and the dropped cleartext setting,
- any native plugin/permission changes.
Run the `ios-release` (and optionally `android-release`) Codemagic workflow, then submit the updated build.
*(This is the one thing I can't do — it needs your Apple/Google credentials.)*

---

## §D — Recommended order
1. **B1 regulatory opinion** (start now — it's the long pole and the biggest risk).
2. **B2 legal review** + **B4 trademark** (parallel, with the same attorney).
3. **Decide audience** (I recommend consumer-first for the Kickstarter) → tell me, and I finish focusing the
   front door.
4. **B7 Cloudflare** (30 min) + **C rebuild** for the rebrand.
5. **B6 Stripe** only if charging; otherwise launch free-during-beta.
6. Launch.

## Still on my plate whenever you want it
- Finish the **audience-focus** pass (demote clinician/legal tools from the consumer front, simplify onboarding)
  once you confirm the direction.
- **Postgres session persistence** (deferred — low severity; a careful, tested change post-launch).
- Implement any **regulatory-opinion changes** from B1.
