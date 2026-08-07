# HumxnMed — Store Assets

Everything for the App Store + Google Play listings, in one place. All HumxnMed-branded (forest + gold).

```
store-assets/
├── apple/
│   ├── AppIcon-1024.png          ← 1024×1024, no alpha, full-bleed (App Store icon)
│   └── screenshots/              ← drop your exported 1290×2796 PNGs here
├── google-play/
│   ├── app-icon-512.png          ← 512×512 (Play "app icon")
│   ├── feature-graphic-1024x500.png  ← required Play banner
│   └── screenshots/              ← same screenshots (min 2, up to 8)
├── logo/                         ← brand marks + wordmarks (horizontal, stacked, dark, social)
└── README.md
```

> **Note:** the *live* App Store / Play icon also comes automatically from your **build** (Codemagic
> generates it from `assets/icon.png`). These files are the clean, correct versions for any **manual**
> upload or reference.

---

## 📸 Screenshots — export these
Open the screenshot set → **https://claude.ai/code/artifact/b79225d9-3ff8-4f9d-a65c-979017804293**
Export each panel (right-click → Inspect → right-click `<div class="shot">` → **Capture node screenshot**),
save the six **1290×2796** PNGs into **both** `apple/screenshots/` and `google-play/screenshots/`.
(Apple: iPhone 6.7". Google Play: min 2 phone screenshots — the same files work.)

---

## 🍎 Apple App Store — checklist + copy
- **Icon:** uploaded via the build (or use `apple/AppIcon-1024.png`).
- **Screenshots:** the six from above (6.7").
- **Name (≤30):** `HumxnMed`
- **Subtitle (≤30):** `Your health, finally explained`
- **Promotional Text (≤170):** Understand your symptoms, results, meds and bills in plain language — in your language. Private by design. Information to help you prepare, never a diagnosis.
- **Keywords (≤100):** `health,symptom,medical,lab results,medication,plain language,translate,caregiver,doctor visit,family`
- **Description:** *(see below — shared with Play)*
- **What's New:** We're now HumxnMed — same mission, clearer name. A cleaner two-part experience (a warm patient app + a clinician point-of-care console), faster performance, accessibility improvements, and 15+ languages.
- **Review note:** "HumxnMed is a plain-language health-information app. No login is required to review the core app. It provides educational information, is not a diagnosis, and is not a medical device."

## 🤖 Google Play — checklist + copy
- **App icon (512×512):** `google-play/app-icon-512.png`
- **Feature graphic (1024×500):** `google-play/feature-graphic-1024x500.png`
- **Phone screenshots:** the six from above.
- **App name (≤30):** `HumxnMed`
- **Short description (≤80):** `Understand your health in plain language — symptoms, labs, meds. Private.`
- **Full description:** *(see below)*

---

## 📝 Shared description (App Store + Google Play full description)
> Health, finally explained — in plain language, in your language.
>
> HumxnMed helps you understand what's confusing about your health: a lab result, a new diagnosis, a
> medication, a bill. Describe what's going on in your own words — any language — and get a clear
> explanation, with what to watch for and good questions for your doctor. It's information to help you
> understand and prepare — not a diagnosis, and never a replacement for your doctor.
>
> WHAT YOU CAN DO
> • Understand symptoms, lab results, medications, and medical bills
> • Ask in any language — HumxnMed answers in yours (15+ languages, read-aloud)
> • Build a private Health Passport for any doctor or ER
> • Track how you feel and get ready for your visits
>
> PRIVATE BY DESIGN
> Your records stay on your device. Never sold, never used for ads. When you use the AI, only what you
> send is processed to answer you.
>
> FOR CLINICIANS
> A separate point-of-care companion — rapid sourced reference, documentation help, and plain-language
> patient communication you independently review. Not a medical device.
>
> HumxnMed is a product of Millennials Creatives LLC. It provides information and education, is not a
> substitute for professional medical advice, and is not a medical device. In an emergency, call your
> local emergency number.

---

## Logo files (`logo/`)
- `app-icon-source-1024.png` — the master icon art
- `logo-horizontal.png` · `logo-stacked.png` · `wordmark.png` — wordmark lockups
- `logo-dark-bg.png` — for dark backgrounds
- `social-share-1200x630.png` — Open Graph / social share card
