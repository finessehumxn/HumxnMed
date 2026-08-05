/* HumxnMed — shared Clinical-tool gate.
   Clinicians TRY before they buy: a 14-day free trial (no card), a founder comp code (free Clinical
   for founding clinicians), then 5 free/month, then the Clinical tier for unlimited. Clinical is its
   own top tier (not consumer Pro). Enforced ONLY when billing gating is ON; otherwise open. */
(function(){
  var cfg={gating:false};
  function testOn(){ try{ return localStorage.getItem('mc_gating_test')==='1'; }catch(e){ return false; } }
  try{ fetch('/billing-config').then(function(r){return r.json();}).then(function(c){ if(c) cfg=c; }).catch(function(){}); }catch(e){}
  function tier(){ try{ return localStorage.getItem('mc_tier')||'free'; }catch(e){ return 'free'; } }
  var FREE_MONTHLY=5, TRIAL_DAYS=14;

  function trial(){
    var start=0; try{ start=parseInt(localStorage.getItem('mc_clinical_trial')||'0',10); }catch(e){}
    if(!start) return {used:false, active:false, daysLeft:0};
    var left=TRIAL_DAYS - Math.floor((Date.now()-start)/86400000);
    return {used:true, active:left>0, daysLeft:Math.max(0,left)};
  }
  function founder(){
    var until=0; try{ until=parseInt(localStorage.getItem('mc_founder_until')||'0',10); }catch(e){}
    return {active: until>Date.now(), daysLeft: until?Math.max(0,Math.ceil((until-Date.now())/86400000)):0};
  }
  window.mcClinicalTrial=trial;
  window.mcFounderStatus=founder;
  window.mcStartClinicalTrial=function(){
    var t=trial();
    if(!t.used){ try{ localStorage.setItem('mc_clinical_trial', String(Date.now())); }catch(e){} t=trial(); }
    var p=document.getElementById('mcProPay'); if(p) p.style.display='none';
    return t;
  };
  // Founder comp code — validated server-side (/redeem-code); grants free Clinical for N days.
  window.mcRedeemFounderCode=function(code){
    return fetch('/redeem-code?code='+encodeURIComponent((code||'').trim()))
      .then(function(r){return r.json();})
      .then(function(d){ if(d&&d.ok){ try{ localStorage.setItem('mc_founder_until', String(Date.now()+(d.days||180)*86400000)); }catch(e){} } return d; })
      .catch(function(){ return {ok:false}; });
  };
  window.mcPromptFounderCode=function(){
    var c=window.prompt('Enter your HumxnMed Clinical founder code:'); if(c==null) return;
    window.mcRedeemFounderCode(c).then(function(d){
      if(d&&d.ok){ alert('✓ Founder access unlocked — Clinical is free for you for '+(d.days||180)+' days. Thank you for being a founding clinician.'); var p=document.getElementById('mcProPay'); if(p) p.style.display='none'; location.reload(); }
      else{ alert('That founder code isn’t valid. Double-check it, or reach out to us.'); }
    });
  };

  function paywall(){
    var t=trial();
    var ex=document.getElementById('mcProPay'); if(ex) ex.remove();
    var d=document.createElement('div'); d.id='mcProPay';
    d.style.cssText='position:fixed;inset:0;z-index:100000;background:rgba(6,20,15,.66);display:flex;align-items:center;justify-content:center;padding:20px';
    var card='<div style="background:#12211a;border:1px solid rgba(255,255,255,.12);border-radius:20px;max-width:400px;width:100%;padding:26px;text-align:center;box-shadow:0 26px 70px rgba(0,0,0,.55);font-family:system-ui,-apple-system,sans-serif;color:#e9f2ec">'
      +'<div style="font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#7fe6b4;background:rgba(52,199,140,.14);border-radius:999px;padding:5px 12px;display:inline-block">HumxnMed Clinical</div>';
    if(!t.used){
      card+='<div style="font-size:21px;font-weight:850;margin:14px 0 6px">Try Clinical free for 14 days</div>'
        +'<div style="font-size:14.5px;color:#cfe3d8;line-height:1.55;margin:0 0 18px">Full access to the point-of-care console, patient handouts, visit summaries &amp; chronologies. <b>No card needed.</b></div>'
        +'<button onclick="window.mcStartClinicalTrial(); location.reload();" style="display:block;width:100%;background:#34c78c;color:#062418;border:none;font-weight:800;font-size:15px;padding:13px;border-radius:12px;cursor:pointer">Start my 14-day free trial &rarr;</button>'
        +'<a href="/founding" style="display:block;color:#8fbfa8;font-size:13px;margin-top:12px;text-decoration:none">or see plans</a>';
    } else {
      card+='<div style="font-size:21px;font-weight:850;margin:14px 0 6px">'+((t.used&&!t.active)?'Your free trial has ended':'You&rsquo;ve used your 5 free this month')+'</div>'
        +'<div style="font-size:14.5px;color:#cfe3d8;line-height:1.55;margin:0 0 18px">Upgrade to <b>HumxnMed Clinical</b> for unlimited patient handouts, visit summaries, and chronologies for your practice.</div>'
        +'<a href="/founding" style="display:block;background:#34c78c;color:#062418;text-decoration:none;font-weight:800;font-size:15px;padding:13px;border-radius:12px">See Clinical plans &rarr;</a>';
    }
    card+='<div style="margin-top:12px"><button onclick="window.mcPromptFounderCode()" style="background:none;border:none;color:#7fe6b4;font-size:13px;text-decoration:underline;cursor:pointer">Have a founder code?</button></div>'
      +'<button onclick="document.getElementById(\'mcProPay\').style.display=\'none\'" style="background:none;border:none;color:#8fbfa8;font-size:13.5px;margin-top:6px;cursor:pointer">Maybe later</button></div>';
    d.innerHTML=card;
    d.addEventListener('click',function(e){ if(e.target===d) d.style.display='none'; });
    document.body.appendChild(d);
  }
  window.mcProGate=function(tool){
    var gating = cfg.gating || testOn();
    if(!gating) return true;                 // gating OFF -> open
    if(tier()==='clinical') return true;     // Clinical tier -> unlimited
    if(founder().active) return true;        // founding-clinician comp -> unlimited
    if(trial().active) return true;          // free trial -> unlimited while active
    var k='mc_pro_used_'+(new Date().toISOString().slice(0,7));
    var used=parseInt(localStorage.getItem(k)||'0',10);
    if(used>=FREE_MONTHLY){ paywall(); return false; }
    try{ localStorage.setItem(k, used+1); }catch(e){}
    return true;
  };
})();
