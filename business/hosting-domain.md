# HumxnMed — Hosting on millennialscreatives.com

**Goal:** serve HumxnMed at **`humxnmed.millennialscreatives.com`** — a subdomain of your existing
company site. No new domain to buy ($0), and it reinforces "HumxnMed, a product of Millennials
Creatives LLC." It runs on your **existing Railway service** via a custom domain (no re-hosting).

---

## Step 1 — Add the custom domain (your side, ~10 min, $0)
1. Railway → the HumxnMed service → **Settings → Networking → Custom Domain**.
2. Add **`humxnmed.millennialscreatives.com`**.
3. Railway shows a **CNAME target** (like `xxxx.up.railway.app`). Add that as a **CNAME record**
   for the `humxnmed` subdomain wherever `millennialscreatives.com`'s DNS is managed.
4. Wait for Railway to show the domain as **verified / SSL issued** (minutes to an hour).
5. Open `https://humxnmed.millennialscreatives.com/app` → the exact same app loads. ✅

The app is already **domain-portable** (all API calls use `location.origin`), so it just works there —
same backend, same keys, no CORS.

---

## Two phases (so nothing breaks)
- **Web = now.** Once the custom domain is verified, the site is live on the branded URL immediately.
  Both URLs work at once (Railway default + the custom domain).
- **Native app = next build.** The shipped App Store app loads from the OLD Railway URL
  (`capacitor.config.json → server.url`). **Keep that URL alive** — do not delete it. On the next
  Codemagic build, change `server.url` to `https://humxnmed.millennialscreatives.com` so the app
  loads from the branded domain.

---

## After the custom domain is verified — flip these to branded (optional, non-urgent)
None of these break anything if left on the Railway URL; do them when convenient:
- [ ] `capacitor.config.json` → `server.url` → `https://humxnmed.millennialscreatives.com` **(do right before the next build, not before the domain is verified)**
- [ ] `frontend/index.html` → `og:image` / `twitter:image` → `https://humxnmed.millennialscreatives.com/static/og-share.png` (share-card image)
- [ ] Stripe payment links → after-payment redirect → `https://humxnmed.millennialscreatives.com/welcome`
- [ ] `EPIC_REDIRECT_URI` env → branded `/app` (only when Epic goes live)

## Email (separate from the web domain — your choice)
Contact addresses in the app are still `team@` / `hello@medcompanionai.com`. Since the brand is now
HumxnMed under Millennials Creatives, you may want `hello@millennialscreatives.com` (or a humxnmed
address). Not urgent; the current ones work. Tell me the address and I'll swap it site-wide.

## Marketing drafts — swept to HumxnMed (done 2026-07-31)
All `store/` drafts + `business/` one-pagers were renamed MedCompanion -> HumxnMed. Functional URLs (Railway) and the working email were intentionally left; update those when the custom domain / new email are live.
