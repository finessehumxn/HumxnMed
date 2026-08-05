# HumxnMed — Turn on customer accounts (passwordless, ~10 min)

Accounts are **built and live in the code but dormant** until a working Supabase project is
connected. The app checks `/auth/status`; until the steps below pass, it shows customers a friendly
"no account needed" message instead of a broken signup. **Nothing here requires a new app build or a
code change from me** — it flips on the moment Supabase is reachable + the table exists.

Why accounts: a purchase gets recorded against the buyer's **email**, so when they sign in with that
same email on any device, their plan unlocks there. We store **only email + tier** server-side —
**health data never leaves the device.** That keeps the privacy story intact.

---

## What's wrong right now
The Railway env already has `SUPABASE_URL` + a key, but they point at a **dead/paused Supabase
project** — that's the `[Errno -2] Name or service not known` your customer hit. Fix = point them at
a **live** project.

## Step 1 — Create (or un-pause) a Supabase project · free
1. supabase.com → **New project** (free tier is fine). Pick a region near your users.
2. Project **Settings → API**, copy:
   - **Project URL** (e.g. `https://abcd1234.supabase.co`)
   - **`service_role` key** (secret — this one)
   - **`anon` key** (optional)

## Step 2 — Set the env vars in Railway · 2 min
Railway → your HumxnMed service → **Variables** → set (replace the dead values):
- `SUPABASE_URL` = your Project URL
- `SUPABASE_SERVICE_KEY` = the `service_role` key
- `SUPABASE_ANON_KEY` = the `anon` key (optional)

Railway redeploys automatically. **Do not paste the service key to me** — set it directly in Railway.

## Step 3 — Create the entitlements table · 1 min
Supabase → **SQL Editor** → run:
```sql
create table if not exists public.entitlements (
  email text primary key,
  tier text not null,
  source text,
  updated_at timestamptz default now()
);
alter table public.entitlements enable row level security;
-- The server uses the service key (bypasses RLS); no public policies needed.
```
(The accounts feature needs only this table. The health-history tables in `supabase_client.py` are
optional and only matter if you later turn on server-side history — off by default.)

## Step 4 — Make the sign-in email send a 6-digit CODE · 2 min
The app uses a typed 6-digit code (works in the app + any browser, no fragile magic-link redirects).
Supabase → **Authentication → Emails → "Magic Link"** template → replace the body with:
```html
<h2>Your HumxnMed sign-in code</h2>
<p>Enter this code in the app to sign in:</p>
<p style="font-size:28px;font-weight:bold;letter-spacing:4px">{{ .Token }}</p>
<p>This code expires in 1 hour. If you didn't request it, ignore this email.</p>
```
The key part is **`{{ .Token }}`** — that's the 6-digit code the app asks for.
Also under **Authentication → Providers → Email**, make sure the **Email** provider is enabled.

## Step 5 — Confirm it's live
- Visit `https://humxnmed.millennialscreatives.com/auth/status` → should say `{"accounts":true}`.
  (It probes that the project is reachable **and** the table exists; caches ~2 min.)
- In the app, click **Sign in** → enter your email → you get a code → enter it → signed in. ✅

---

## ⚠️ Email volume (read before real launch)
Supabase's **built-in** auth email is rate-limited (only a few per hour) and is meant for testing.
Before you drive real signups, set **custom SMTP**: Supabase → **Project Settings → Authentication →
SMTP Settings** → plug in a transactional provider (Resend, Postmark, SendGrid, or even your
Google Workspace SMTP). Free until then, but codes will throttle under load.

## How a purchase ties to the account
1. Customer buys via Stripe → Stripe knows their email.
2. `/verify-purchase` records `email → tier` in `entitlements`.
3. On `/welcome`, they're invited to "Secure my account" with that same email.
4. They sign in with the code → `/auth/verify-code` looks up their tier → unlocks it on that device.
5. Sign in with that email on another device → same unlock. Plan follows them.

**Match the emails.** Tell customers to use the **same email** for the account as at checkout, or the
purchase won't match. The `/welcome` page prefills their Stripe email to make this automatic.
