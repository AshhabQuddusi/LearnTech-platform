/**
 * LearnTech main.js v4 — 8-bit Arcade
 */
document.addEventListener('DOMContentLoaded', () => {
  initNav(); initReveal(); initCounter();
  initVideoModal(); initAuth(); initSearch();
  restoreAuth(); initXPBars();
});

function initNav() {
  const tog = document.querySelector('.nav-toggle');
  const lnk = document.querySelector('.nav-links');
  tog?.addEventListener('click', () => {
    const o = tog.classList.toggle('open');
    lnk?.classList.toggle('open', o);
    tog.setAttribute('aria-expanded', String(o));
  });
  lnk?.querySelectorAll('a').forEach(a =>
    a.addEventListener('click', () => { tog?.classList.remove('open'); lnk.classList.remove('open'); }));
  const path = location.pathname;
  lnk?.querySelectorAll('a[href]').forEach(a => {
    const h = a.getAttribute('href');
    a.classList.toggle('active', h === '/' ? path === '/' : path.startsWith(h) && h !== '/');
  });
  // Scrolled state
  window.addEventListener('scroll', () =>
    document.querySelector('.nav')?.classList.toggle('scrolled', window.scrollY > 28), { passive: true });
}

function initReveal() {
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); io.unobserve(e.target); } });
  }, { threshold: 0.09, rootMargin: '0px 0px -24px 0px' });
  document.querySelectorAll('.reveal, .stagger').forEach(el => io.observe(el));
}
window.LT_reveal = () => {
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); io.unobserve(e.target); } });
  }, { threshold: 0.07 });
  document.querySelectorAll('.reveal:not(.revealed),.stagger:not(.revealed)').forEach(el => io.observe(el));
};

function initCounter() {
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const el=e.target, target=+el.dataset.count, sfx=el.dataset.suffix||'';
      const dur=1800, t0=performance.now();
      const tick = now => {
        const p=Math.min((now-t0)/dur,1), v=1-Math.pow(1-p,3);
        el.textContent=Math.round(target*v).toLocaleString()+sfx;
        if(p<1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      io.unobserve(el);
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('[data-count]').forEach(el => io.observe(el));
}

/* XP bars animate in on scroll */
function initXPBars() {
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const bar = e.target.querySelector('.xp-bar');
      if (bar) {
        const target = bar.dataset.xp || '70';
        bar.style.width = '0%';
        setTimeout(() => { bar.style.width = target + '%'; }, 100);
      }
      io.unobserve(e.target);
    });
  }, { threshold: 0.3 });
  document.querySelectorAll('.xp-wrap').forEach(el => io.observe(el));
}

function initVideoModal() {
  const el = document.createElement('div');
  el.className = 'video-modal-overlay'; el.id = 'vmodal';
  el.setAttribute('role','dialog'); el.setAttribute('aria-modal','true');
  el.innerHTML = `
    <div class="video-modal-box">
      <div class="video-modal-header">
        <span class="video-modal-title" id="vmodal-title">NOW PLAYING</span>
        <button class="video-modal-close" id="vmodal-close" aria-label="Close">✕</button>
      </div>
      <div class="video-modal-ratio">
        <iframe id="vmodal-iframe" allowfullscreen allow="autoplay;encrypted-media" title="Video"></iframe>
      </div>
    </div>`;
  document.body.appendChild(el);
  const iframe=document.getElementById('vmodal-iframe');
  const title=document.getElementById('vmodal-title');
  const close=document.getElementById('vmodal-close');
  const open=(id,t)=>{ iframe.src=`https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`; title.textContent=t||'NOW PLAYING'; el.classList.add('open'); document.body.style.overflow='hidden'; };
  const shut=()=>{ el.classList.remove('open'); setTimeout(()=>{iframe.src=''},300); document.body.style.overflow=''; };
  close.addEventListener('click',shut);
  el.addEventListener('click',e=>{if(e.target===el)shut();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')shut();});
  window.LT_openVideo=open;
}

function initAuth() {
  const ov=document.getElementById('auth-modal'); if(!ov) return;
  const tabs=ov.querySelectorAll('[data-auth-tab]');
  const forms=ov.querySelectorAll('[data-auth-form]');
  const err=ov.querySelector('[data-auth-error]');
  const closeM=()=>{ov.classList.remove('open');if(err)err.textContent='';};
  const showE=m=>{if(err)err.textContent=m;};
  const switchTab=t=>{
    tabs.forEach(b=>{b.classList.toggle('active',b.dataset.authTab===t);b.setAttribute('aria-selected',String(b.dataset.authTab===t));});
    forms.forEach(f=>f.classList.toggle('hidden',f.dataset.authForm!==t));
    if(err)err.textContent='';
  };
  document.querySelectorAll('[data-open-auth]').forEach(b=>b.addEventListener('click',()=>{switchTab(b.dataset.openAuth||'login');ov.classList.add('open');}));
  ov.querySelector('[data-auth-close]')?.addEventListener('click',closeM);
  ov.addEventListener('click',e=>{if(e.target===ov)closeM();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeM();});
  tabs.forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.authTab)));
  ov.querySelector('[data-auth-form="login"] form')?.addEventListener('submit',async e=>{
    e.preventDefault(); const fd=new FormData(e.target);
    try{const r=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:fd.get('email'),password:fd.get('password')})});const d=await r.json();if(d.ok){onAuth(d);closeM();showToast('WELCOME BACK, '+d.name.split(' ')[0].toUpperCase()+'!','success');}else showE(d.error||'LOGIN FAILED');}catch{showE('CONNECTION ERROR');}
  });
  ov.querySelector('[data-auth-form="register"] form')?.addEventListener('submit',async e=>{
    e.preventDefault(); const fd=new FormData(e.target);
    if(fd.get('password')!==fd.get('password2')){showE("PASSWORDS DON'T MATCH");return;}
    try{const r=await fetch('/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:fd.get('name'),email:fd.get('email'),password:fd.get('password')})});const d=await r.json();if(d.ok){onAuth(d);closeM();showToast('ACCOUNT CREATED! +50 XP 🎉','success');}else showE(d.error||'REGISTRATION FAILED');}catch{showE('CONNECTION ERROR');}
  });
}
function onAuth(d){sessionStorage.setItem('lt_user',JSON.stringify({name:d.name,premium:d.premium}));restoreAuth();}
function restoreAuth(){
  const raw=sessionStorage.getItem('lt_user');if(!raw)return;const u=JSON.parse(raw);
  const lb=document.querySelector('[data-open-auth="login"]');if(lb)lb.style.display='none';
  const chip=document.getElementById('nav-user-chip');const lbl=document.getElementById('nav-user-name');const av=document.getElementById('nav-avatar');
  if(chip)chip.style.display='flex';
  if(lbl)lbl.textContent=u.name.split(' ')[0].toUpperCase();
  if(av)av.textContent=u.name.charAt(0).toUpperCase();
}

function initSearch(){
  const input=document.getElementById('global-search');const drop=document.getElementById('search-results');if(!input||!drop)return;
  let t;
  input.addEventListener('input',()=>{clearTimeout(t);const q=input.value.trim();if(!q){drop.innerHTML='';drop.hidden=true;return;}t=setTimeout(()=>doSearch(q),255);});
  document.addEventListener('click',e=>{if(!input.closest('.search-container')?.contains(e.target))drop.hidden=true;});
  async function doSearch(q){
    drop.innerHTML='<div class="search-loading">SEARCHING...</div>';drop.hidden=false;
    try{
      const d=await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=8`).then(r=>r.json());
      if(!d.length){drop.innerHTML='<div class="search-empty">NO RESULTS FOUND</div>';return;}
      drop.innerHTML=d.map(i=>`<a href="${i.url}" class="search-result-item" target="${i.url!=='#'?'_blank':'_self'}" rel="noopener">
        <span class="badge badge-${typeClr(i.type)}">${i.type}</span>
        <div style="flex:1;min-width:0"><div class="search-result-title">${i.title}</div><div class="search-result-source">${i.source}</div></div>
        ${i.premium?'<span class="badge badge-gold">★</span>':''}</a>`).join('');
    }catch{drop.innerHTML='<div class="search-empty">SEARCH UNAVAILABLE</div>';}
  }
}
function typeClr(t){return{docs:'blue',article:'blue',guide:'orange',paper:'pink',course:'green',book:'blue'}[t]||'gray';}

function showToast(msg,type='success'){
  let t=document.querySelector('.toast');
  if(!t){t=document.createElement('div');t.className='toast';document.body.appendChild(t);}
  const icon=type==='success'?'✓':type==='error'?'✕':'!';
  const col=type==='success'?'var(--green)':type==='error'?'var(--red)':'var(--orange)';
  t.className=`toast ${type}`;
  t.innerHTML=`<span style="color:${col};font-size:0.9rem">${icon}</span>${msg}`;
  requestAnimationFrame(()=>{t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3600);});
}
window.showToast=showToast;

document.addEventListener('submit',async e=>{
  if(!e.target.matches('#contact-form'))return;
  e.preventDefault();
  const fd=new FormData(e.target);const btn=e.target.querySelector('button[type="submit"]');
  if(btn){btn.disabled=true;btn.textContent='SENDING...';}
  try{const r=await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:fd.get('name'),email:fd.get('email'),message:fd.get('message')})});const d=await r.json();if(d.ok){showToast('MESSAGE SENT! +10 XP 📬','success');e.target.reset();}else showToast('ERROR — TRY AGAIN','error');}
  catch{showToast('CONNECTION ERROR','error');}
  finally{if(btn){btn.disabled=false;btn.textContent='SEND MESSAGE';}}
});
