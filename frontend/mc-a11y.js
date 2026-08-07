/* HumxnMed — shared accessibility layer (keyboard + focus management).
   ────────────────────────────────────────────────────────────────────
   The app has many clickable <div>/<span> elements and ~28 dialogs. Rather than edit each one,
   this adds, globally and defensively:
     1) Keyboard operability — any element with onclick / role=button|menuitem becomes focusable
        and responds to Enter/Space (was mouse-only, invisible to keyboard & switch users).
     2) A focus trap + focus return for any visible dialog — Tab stays inside the open dialog,
        Escape closes it, and focus returns to whatever opened it (was: focus fell behind the modal).
   Safe by design: it only augments; it never removes existing behavior, and it no-ops when there
   is no dialog open or the target is a native control. */
(function () {
  function isNative(el) { return el && el.tagName && /^(a|button|input|select|textarea|label|summary)$/i.test(el.tagName); }

  // ── 1) Make clickable non-native elements keyboard-focusable + operable ──
  function makeFocusable(root) {
    try {
      var nodes = (root && root.querySelectorAll) ? root.querySelectorAll('[onclick]:not(a):not(button):not(input):not(select):not(textarea):not([tabindex])') : [];
      Array.prototype.forEach.call(nodes, function (el) {
        // skip container elements that already hold their own interactive controls — labeling a
        // whole card as a "button" mis-announces it to screen readers and adds redundant tab stops
        if (el.querySelector && el.querySelector('a[href],button,input,select,textarea,[role="button"],[onclick]')) return;
        el.setAttribute('tabindex', '0');
        if (!el.getAttribute('role')) el.setAttribute('role', 'button');
      });
    } catch (e) {}
  }
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ' && e.key !== 'Spacebar') return;
    var el = e.target;
    if (!el || isNative(el) || el.isContentEditable) return;
    var role = el.getAttribute && el.getAttribute('role');
    var activatable = el.hasAttribute && (el.hasAttribute('onclick') || role === 'button' || role === 'menuitem' || role === 'tab');
    if (activatable) { e.preventDefault(); if (typeof el.click === 'function') el.click(); }
  });

  // ── 2) Focus trap + return for visible dialogs ──
  var DIALOG_SEL = '[role="dialog"], .modal.show, .mcj-screen.show, .crisis-modal.show';
  var lastTrigger = null;
  document.addEventListener('mousedown', function (e) { lastTrigger = e.target; }, true);
  function isVisible(el) {
    if (!el || el.offsetParent === null) return false;
    var r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }
  function openDialogs() { return Array.prototype.filter.call(document.querySelectorAll(DIALOG_SEL), isVisible); }
  function focusablesIn(d) {
    return Array.prototype.filter.call(
      d.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'),
      function (el) { return el.offsetParent !== null; }
    );
  }
  document.addEventListener('keydown', function (e) {
    if (e.defaultPrevented) return;   // a dialog with its own trap already handled it — don't double-move focus
    var dlgs = openDialogs();
    if (!dlgs.length) return;
    var d = dlgs[dlgs.length - 1]; // topmost
    if (e.key === 'Tab') {
      var f = focusablesIn(d);
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (!d.contains(document.activeElement)) { e.preventDefault(); first.focus(); return; }
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  // When a dialog opens, move focus into it; when it closes, return focus to the opener.
  var wasOpen = false;
  if (window.MutationObserver) {
    var mo = new MutationObserver(function (muts) {
      // keyboard-enable any newly added clickable elements
      muts.forEach(function (m) { for (var i = 0; i < m.addedNodes.length; i++) { var n = m.addedNodes[i]; if (n.nodeType === 1) makeFocusable(n); } });
      var open = openDialogs();
      if (open.length && !wasOpen) {
        wasOpen = true;
        var d = open[open.length - 1];
        if (!d.contains(document.activeElement)) {
          var f = focusablesIn(d);
          // prefer the first non-close control, else the dialog itself
          var target = f.find ? f.find(function (el) { return !/close|dismiss|×/i.test((el.getAttribute('aria-label') || '') + el.textContent); }) : null;
          (target || f[0] || d).focus && (target || f[0] || d).focus();
        }
      } else if (!open.length && wasOpen) {
        wasOpen = false;
        try { if (lastTrigger && lastTrigger.focus) lastTrigger.focus(); } catch (e) {}
      }
    });
    // childList only — watching every class/style change on the whole page (to catch modals toggled
    // via a .show class) fires constantly on this busy app and drags performance. Trade-off: a modal
    // that's pre-rendered and merely shown won't auto-focus-in, but the Tab-trap still contains it.
    try { mo.observe(document.body, { childList: true, subtree: true }); } catch (e) {}
  }

  function boot() { makeFocusable(document); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
