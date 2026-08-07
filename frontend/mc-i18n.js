/* HumxnMed — UI localization engine (default-safe).
   ─────────────────────────────────────────────────
   The app is authored in English. This layer translates the *interface chrome* into the
   user's language ONLY when they explicitly pick one (or their device is set to one). English
   stays the untouched default — if this file fails, is skipped, or a string is missing, the
   user sees English, never a blank.

   SAFETY (this is a health app):
   • Anything marked  .mc-authoritative | [data-i18n-keep] | [translate="no"]  is NEVER
     machine-translated — that's where medical/legal disclaimers and safety warnings live,
     and where AI-generated medical output is shown. English there is authoritative.
   • Pure numbers, medical codes, drug names, URLs, emails and emoji are left as-is.
   • A persistent notice tells users the UI is machine-translated and English is official. */
(function () {
  var SUPPORTED = {es:1,fr:1,zh:1,ar:1,hi:1,pt:1,ru:1,vi:1,ko:1,tl:1,de:1,ja:1,fa:1,so:1};
  var RTL = {ar:1, fa:1};
  var SKIP_TAGS = {SCRIPT:1,STYLE:1,NOSCRIPT:1,CODE:1,PRE:1,TEXTAREA:1,KBD:1,SAMP:1,SELECT:1,OPTION:1,INPUT:1};
  var SKIP_SEL = '[data-i18n-keep],.mc-authoritative,[data-no-translate],[translate="no"],[contenteditable="true"]';
  var LANGS = [['en','English'],['es','Español'],['fr','Français'],['zh','中文'],['ar','العربية'],
               ['hi','हिन्दी'],['pt','Português'],['ru','Русский'],['vi','Tiếng Việt'],['ko','한국어'],
               ['tl','Tagalog'],['de','Deutsch'],['ja','日本語'],['fa','فارسی'],['so','Soomaali']];

  function detect() {
    try {
      var q = new URLSearchParams(location.search).get('lang');
      if (q !== null) { q = (q || '').toLowerCase(); if (q === '' || q === 'en') { localStorage.setItem('mc_ui_lang','en'); return 'en'; } if (SUPPORTED[q]) { localStorage.setItem('mc_ui_lang', q); return q; } }
      var s = localStorage.getItem('mc_ui_lang'); if (s) return (s === 'en' || SUPPORTED[s]) ? s : 'en';
      var n = (navigator.language || '').slice(0,2).toLowerCase(); if (SUPPORTED[n]) return n;
    } catch (e) {}
    return 'en';
  }
  var LANG = detect();
  // Route AI RESPONSES into the same language natively (best quality) rather than
  // re-translating medical output. Set as early as possible, before any AI call.
  if (LANG !== 'en') { try { window.currentLang = LANG; } catch (e) {} }

  function loadCache(l) { try { return JSON.parse(localStorage.getItem('mc_i18n_' + l) || '{}'); } catch (e) { return {}; } }
  function saveCache() { try { localStorage.setItem('mc_i18n_' + LANG, JSON.stringify(CACHE)); } catch (e) {} }
  var CACHE = LANG === 'en' ? {} : loadCache(LANG);

  // SAFETY: never machine-translate safety-critical copy. A mistranslated crisis line, emergency
  // instruction, or medical disclaimer can cause harm, so these stay authoritative English until a
  // human-reviewed translation exists. (Better English-and-clear than translated-and-wrong.)
  var SAFETY_RE = /988|911|suicide|crisis lifeline|not a (diagnosis|doctor|medical device|substitute|replacement)|not an emergency|call your local emergency|seek emergency|emergency room|go to the er|get help right away|call emergency/i;

  function translatable(str) {
    if (!str) return false;
    var s = str.trim();
    if (s.length < 2) return false;
    if (!/[A-Za-zÀ-ɏ]/.test(s)) return false;      // must contain letters (skip numbers/codes/emoji)
    if (/^[\d\s.,:%\/\-+°x×()]+$/.test(s)) return false;     // pure numeric / units
    if (/^https?:\/\//i.test(s) || /^\S+@\S+\.\S+$/.test(s)) return false; // url / email
    if (SAFETY_RE.test(s)) return false;            // keep safety-critical copy in authoritative English
    return true;
  }
  function skip(node) {
    var el = node.nodeType === 3 ? node.parentNode : node;
    for (var p = el; p && p !== document.documentElement; p = p.parentNode) {
      if (p.nodeType !== 1) continue;
      if (SKIP_TAGS[p.tagName]) return true;
      if (p.matches && p.matches(SKIP_SEL)) return true;
    }
    return false;
  }

  function textItem(node) {
    var raw = node.nodeValue, tr = raw.trim(), i = raw.indexOf(tr);
    var lead = raw.slice(0, i), trail = raw.slice(i + tr.length);
    return { text: tr, apply: function (t) { node.nodeValue = lead + t + trail; } };
  }
  function collect(root) {
    var items = [];
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: function (n) {
      if (!n.nodeValue || !translatable(n.nodeValue)) return NodeFilter.FILTER_REJECT;
      if (skip(n)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }});
    var n; while (n = w.nextNode()) items.push(textItem(n));
    var scope = (root.nodeType === 1 && root.querySelectorAll) ? root : document;
    var attrEls = Array.prototype.slice.call(scope.querySelectorAll('[placeholder],[aria-label],[title],[alt]'));
    if (root.nodeType === 1 && root.matches && root.matches('[placeholder],[aria-label],[title],[alt]')) attrEls.unshift(root);
    attrEls.forEach(function (el) {
      if (skip(el)) return;
      ['placeholder','aria-label','title','alt'].forEach(function (a) {
        var v = el.getAttribute && el.getAttribute(a);
        if (v && translatable(v)) items.push({ text: v.trim(), apply: (function (elm, attr) { return function (t) { elm.setAttribute(attr, t); }; })(el, a) });
      });
    });
    return items;
  }

  function translateItems(items) {
    if (LANG === 'en' || !items.length) return;
    var need = [], seen = {};
    items.forEach(function (it) {
      var c = CACHE[it.text];
      if (c) it.apply(c);
      else if (!seen[it.text]) { seen[it.text] = 1; need.push(it.text); }
    });
    if (!need.length) return;
    function applyCached() { items.forEach(function (it) { var c = CACHE[it.text]; if (c) it.apply(c); }); }
    // Chunk the network requests so text appears PROGRESSIVELY (each chunk applies as it
    // returns) instead of the whole page staying English until one big request finishes.
    var CH = 40;
    for (var i = 0; i < need.length; i += CH) {
      (function (chunk) {
        fetch('/i18n-batch', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ strings: chunk, target: LANG }) })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            var tr = (d && d.translations) || {}, changed = false;
            for (var k in tr) { if (tr[k] && tr[k] !== k) { CACHE[k] = tr[k]; changed = true; } }
            if (changed) saveCache();
            applyCached();
          })
          .catch(function () {});
      })(need.slice(i, i + CH));
    }
  }

  function run(root) { if (LANG === 'en') return; try { translateItems(collect(root || document.body)); } catch (e) {} }

  function notice() {
    if (LANG === 'en' || document.getElementById('mcI18nNote')) return;
    var b = document.createElement('div'); b.id = 'mcI18nNote'; b.setAttribute('data-i18n-keep','');
    b.setAttribute('role','note');
    b.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:99998;background:#0a1f1a;color:#cfe3d8;font:12px/1.4 system-ui,-apple-system,sans-serif;padding:7px 12px 7px;text-align:center;box-shadow:0 -2px 10px rgba(0,0,0,.25)';
    // Kept English on purpose (authoritative safety notice). Short + universal.
    b.innerHTML = 'Machine-translated interface · English is the official version · In an emergency call your local emergency number · <button type="button" id="mcI18nEn" style="background:none;border:none;color:#7fe6b4;text-decoration:underline;cursor:pointer;font:inherit;padding:0">English</button>';
    document.body.appendChild(b);
    var en = document.getElementById('mcI18nEn');
    if (en) en.onclick = function () { try { localStorage.setItem('mc_ui_lang','en'); } catch (e) {} var u = new URL(location.href); u.searchParams.delete('lang'); location.href = u.toString(); };
  }

  function switcher() {
    if (document.getElementById('mcLangBar')) return;
    var wrap = document.createElement('div'); wrap.id = 'mcLangBar'; wrap.setAttribute('data-i18n-keep','');
    wrap.style.cssText = 'position:fixed;bottom:' + (LANG === 'en' ? '14px' : '40px') + ';' + (RTL[LANG] ? 'right' : 'left') + ':14px;z-index:99999';
    var sel = document.createElement('select');
    sel.setAttribute('aria-label','Choose language / Seleccionar idioma');
    sel.style.cssText = 'font:600 13px system-ui,-apple-system,sans-serif;padding:8px 10px;border-radius:10px;border:1px solid rgba(0,0,0,.25);background:#fff;color:#123;box-shadow:0 4px 14px rgba(0,0,0,.2);cursor:pointer;max-width:160px';
    LANGS.forEach(function (l) { var o = document.createElement('option'); o.value = l[0]; o.textContent = '🌐 ' + l[1]; if (l[0] === LANG) o.selected = true; sel.appendChild(o); });
    sel.onchange = function () { try { localStorage.setItem('mc_ui_lang', sel.value); } catch (e) {} var u = new URL(location.href); u.searchParams.delete('lang'); location.href = u.toString(); };
    wrap.appendChild(sel); document.body.appendChild(wrap);
  }

  function observe() {
    if (LANG === 'en' || !window.MutationObserver) return;
    var pending = [], timer = null;
    var mo = new MutationObserver(function (muts) {
      for (var i = 0; i < muts.length; i++) { var a = muts[i].addedNodes; for (var j = 0; j < a.length; j++) { var nd = a[j]; if (nd.nodeType === 1 || nd.nodeType === 3) pending.push(nd); } }
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        var batch = pending.splice(0), items = [];
        batch.forEach(function (nd) {
          if (nd.nodeType === 1) { if (!skip(nd)) items = items.concat(collect(nd)); }
          else if (nd.nodeType === 3 && translatable(nd.nodeValue) && !skip(nd)) items.push(textItem(nd));
        });
        translateItems(items);
      }, 300);
    });
    mo.observe(document.body, { childList: true, subtree: true });
  }

  // Modest RTL fixes for Arabic/Farsi (scoped to [dir="rtl"], so LTR is never touched). Not a full
  // RTL redesign, but corrects text alignment, list bullets, inputs and the language switcher.
  function injectRTL() {
    if (document.getElementById('mcRTLcss')) return;
    var s = document.createElement('style'); s.id = 'mcRTLcss';
    s.textContent =
      '[dir="rtl"] body,[dir="rtl"] .wrap,[dir="rtl"] p,[dir="rtl"] li,[dir="rtl"] h1,[dir="rtl"] h2,[dir="rtl"] h3{text-align:right}' +
      '[dir="rtl"] input,[dir="rtl"] textarea,[dir="rtl"] select{text-align:right;direction:rtl}' +
      '[dir="rtl"] ul,[dir="rtl"] ol{padding-right:1.2em;padding-left:0}' +
      '[dir="rtl"] .price li,[dir="rtl"] .step{padding-right:22px;padding-left:0}' +
      '[dir="rtl"] .price li::before{right:2px;left:auto}' +
      '[dir="rtl"] #mcLangBar{left:auto !important;right:14px}';
    (document.head || document.documentElement).appendChild(s);
  }
  function start() {
    if (LANG !== 'en') {
      document.documentElement.lang = LANG;
      if (RTL[LANG]) { document.documentElement.dir = 'rtl'; injectRTL(); }
      else { document.documentElement.dir = 'ltr'; }
    }
    run(document.body);
    switcher();
    notice();
    observe();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  window.mcI18n = { lang: LANG, run: run };
})();
