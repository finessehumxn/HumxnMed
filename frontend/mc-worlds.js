/* HumxnMed — "two worlds" front door.
   One app, two experiences. First-time visitors pick their world; the choice is remembered and they
   land straight in it next time. Self-contained + additive: if this file fails to load, the app just
   opens normally. Loaded on the patient entry (/app). */
(function () {
  var KEY = 'mc_world';
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(w) { try { localStorage.setItem(KEY, w); } catch (e) {} }
  function closeDoor() { var d = document.getElementById('mcWorldDoor'); if (d) d.remove(); }
  function choose(w) { set(w); if (w === 'clinician') { location.href = '/console'; } else { closeDoor(); } }

  function door() {
    if (document.getElementById('mcWorldDoor')) return;
    var d = document.createElement('div');
    d.id = 'mcWorldDoor';
    d.setAttribute('role', 'dialog'); d.setAttribute('aria-modal', 'true'); d.setAttribute('aria-label', 'Who is here today?');
    d.setAttribute('data-i18n-keep', '');
    d.style.cssText = 'position:fixed;inset:0;z-index:100002;background:linear-gradient(165deg,#0B3D2E,#0A1F1A);display:flex;align-items:center;justify-content:center;padding:24px;overflow:auto';
    d.innerHTML =
      '<div style="max-width:540px;width:100%;text-align:center;font-family:system-ui,-apple-system,sans-serif;color:#eaf3ee">' +
        '<div style="font-size:13px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#7fe6b4">HumxnMed</div>' +
        '<h1 style="font-family:Lora,Georgia,serif;font-size:30px;font-weight:800;margin:12px 0 8px;text-wrap:balance">Who’s here today?</h1>' +
        '<p style="color:#a9d6c2;font-size:15px;line-height:1.5;margin:0 0 26px">Two experiences, one place. Pick yours — you can switch anytime.</p>' +
        '<div style="display:grid;gap:14px">' +
          '<button id="mcWpatient" type="button" style="text-align:left;background:#F5F1E6;color:#123227;border:none;border-radius:18px;padding:20px 22px;cursor:pointer;font-family:inherit;box-shadow:0 12px 30px rgba(0,0,0,.3)">' +
            '<div style="font-size:21px;font-weight:850">🙋‍ For me &amp; my family</div>' +
            '<div style="font-size:14px;color:#3a4b42;margin-top:5px;line-height:1.5">Understand your health in plain language — symptoms, results, medications, and getting ready for your visits.</div></button>' +
          '<button id="mcWclin" type="button" style="text-align:left;background:#0f1f18;color:#eaf3ee;border:1px solid rgba(127,230,180,.4);border-radius:18px;padding:20px 22px;cursor:pointer;font-family:inherit">' +
            '<div style="font-size:21px;font-weight:850">🩺 I’m a clinician</div>' +
            '<div style="font-size:14px;color:#a9d6c2;margin-top:5px;line-height:1.5">Point-of-care console — rapid reference, documentation, patient communication, and evidence you review.</div></button>' +
        '</div>' +
        '<div style="font-size:12px;color:#6f9a86;margin-top:20px">You can change this anytime from the menu.</div>' +
      '</div>';
    document.body.appendChild(d);
    var pb = document.getElementById('mcWpatient'), cb = document.getElementById('mcWclin');
    pb.onclick = function () { choose('patient'); };
    cb.onclick = function () { choose('clinician'); };
    pb.focus();
  }

  // Re-open the door (used by a "Switch experience" control anywhere in the app).
  window.mcSwitchWorld = function () { try { localStorage.removeItem(KEY); } catch (e) {} door(); };

  function returningClinicianBanner() {
    if (document.getElementById('mcWorldBanner')) return;
    var b = document.createElement('div'); b.id = 'mcWorldBanner'; b.setAttribute('data-i18n-keep', '');
    b.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:99997;background:#0B3D2E;color:#eafaf1;font:13px/1.4 system-ui,-apple-system,sans-serif;padding:9px 14px;text-align:center;box-shadow:0 -2px 12px rgba(0,0,0,.3)';
    b.innerHTML = 'You’re in the patient world. <a href="/console" style="color:#7fe6b4;font-weight:700;text-decoration:none">Go to the Clinician console →</a> ' +
      '<button type="button" onclick="this.parentNode.remove()" aria-label="Dismiss" style="background:none;border:none;color:#a9d6c2;margin-left:8px;cursor:pointer;font-size:15px">×</button>';
    document.body.appendChild(b);
  }

  function boot() {
    var w = get();
    if (!w) { door(); return; }
    if (w === 'clinician') returningClinicianBanner();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
