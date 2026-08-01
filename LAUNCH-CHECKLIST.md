# HumxnMed — Launch Checklist (the one doc)

**The product is built, rebranded, and LIVE.** Everything below is **account setup you do** —
no more coding required. Do it top to bottom. Time estimates included. Nothing here can break the
live app; every risky step has an instant rollback.

---

## Where things stand (all ✅ done)
- App + all pages live and rebranded **HumxnMed**
- Logo corrected everywhere (web live now; **App Store icon applies on the next build**)
- Four tiers (Free / Plus / Pro / Clinical) + billing engine — built & verified
- Medication + appointment reminders and Apple IAP — **staged** (activate on the next build)
- Web-purchase auto-unlock, referral links, Terms + Privacy — done
- Marketing drafts swept to HumxnMed

---

## 1 · Custom domain — 10 min · $0
Railway → your service → **Settings → Networking → Custom Domain** → add
`humxnmed.millennialscreatives.com` → add the CNAME it shows to your DNS.
**Keep the old Railway URL alive** (the shipped app loads from it until step 2). *(details: `business/hosting-domain.md`)*

## 2 · The one build (Codemagic) — ~1 hr, mostly waiting
Run the **`ios-release`** workflow. This single build:
- applies the **new HumxnMed app name + HM icon**
- activates **reminders** (meds + appointments) and the **Apple IAP** plugin
- uploads to App Store Connect → push to TestFlight / Review
*(optional: run `android-release` for a signed `.aab`)*

## 3 · App Store Connect — ~20 min
- App **name** → `HumxnMed`
- **Subtitle** → `AI health & meds companion`
- **Keywords** → medication tracker, meds, health, caregiver, medical, family, pharmacy, symptoms
- Refresh any **screenshots** showing the old name/logo
- Privacy URL keeps working (Railway now, or the new domain later)

## 4 · Billing — ONLY if charging at launch *(else skip — the app stays free for everyone)*
**4a. Stripe (web):** Plus & Clinical links already work ✅. Create the 3 **Pro** products
(`$24.99 / $149.99 / $299.99`) → **send me the links, I wire them (5 min).**
Optional: set `STRIPE_SECRET_KEY` + each link's after-payment redirect to `/welcome` → web auto-unlock.
**4b. Apple IAP:** ASC products `mc_plus_*` / `mc_pro_*` / `mc_clinical_*` · RevenueCat entitlements
named `plus` / `pro` / `clinical` + `appl_…` key · Railway `RC_PUBLIC_KEY`. Sandbox-test one purchase.
**4c. Flip on:** Railway `MC_GATING = 1`. **Rollback anytime:** `MC_GATING = 0`.
*(full detail: `business/ios-iap-setup.md`, `business/go-live-build-checklist.md`)*

> ⚠️ Because the live app is iOS, don't flip `MC_GATING=1` until **4b** is done + a new build ships —
> otherwise iPhone users hit paywalls they can't pay through. Web-only is fine to gate earlier.

## 5 · Trademark — attorney
Clearance opinion on **HumxnMed**, then file (classes **9 / 42 / 44**, owner **Millennials Creatives LLC**).
Your live App Store app is your specimen of use.

## 6 · Marketing channels — your pace
Update LinkedIn, the Millennials Creatives site, and any articles to HumxnMed + the new logo.
Ready-to-paste copy is in the (already-swept) `store/` drafts.

---

## What I can still do for you (just say the word)
- **Email swap** site-wide — give me the address (e.g. `hello@millennialscreatives.com`)
- **Wire Pro checkout** — the moment you paste the 3 Pro Stripe links
- **Align RevenueCat entitlements** to the code if a sandbox purchase doesn't unlock (send the customer-info string)

## Recommended path
Launch **free** now (skip step 4) → build users + testimonials → add billing when ready. The setup is
identical whenever you do it, and a free launch strengthens both the trademark and any future raise.
