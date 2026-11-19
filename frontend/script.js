// no-scam: standalone scripted demo. No API calls or real message scanning.
const sampleMessage = {
  sender: 'Amir (Son)',
  familiarContact: true,
  text: "Hi Mak, it's me Amir. I need your help urgently! My bank account has a problem and I need to pay RM500 right now. Please use this link to help me: https://urgent-family-pay.example Please don't call me, I'm in a meeting. Just do it quickly!"
};

// Simple, explainable rules for one fictional demonstration scenario.
// Results indicate caution, never confirm a scam or legitimate identity.
function getWarningSignals(message) {
  const t = message.text.toLowerCase();
  const signals = [];
  if (/urgently|right now|quickly|immediately|segera/.test(t)) signals.push({icon:'⏱',title:'Pressure to act quickly',detail:'The message says it is urgent and asks you to act before checking.'});
  if (/https?:\/\/\S+/.test(t)) signals.push({icon:'🔗',title:'Link has not been verified',detail:'The payment link is not a destination we have independently checked.'});
  if (/rm\s*\d+|pay|transfer|bank account/.test(t)) signals.push({icon:'💳',title:'Unusual money request',detail:'You are being asked to send money or use a payment link.'});
  if (/don't call|do not call|don't tell|keep.*secret/.test(t)) signals.push({icon:'🙊',title:'Discourages independent verification',detail:'The sender asks you not to call, making it harder to check who is really asking.'});
  return signals;
}

const screens = ['incoming','assessment','decision','recovery'];
const titles = {
  incoming:['Hello, Salmah 👋',"Your safety matters. Let's check before you act."],
  assessment:['Your watchdog is here 🐶',"Let's understand what seems unusual."],
  decision:['You have options 💚','You can pause and verify before doing anything.'],
  recovery:['Help is here 💙','These next steps can help you respond safely.']
};
function navigate(to) {
  if (!screens.includes(to)) return;
  screens.forEach(id => {document.getElementById(id).hidden = id !== to;});
  document.querySelectorAll('[data-step]').forEach(el=>{
    const index = screens.indexOf(el.dataset.step);
    el.classList.toggle('current',index===screens.indexOf(to));
    el.classList.toggle('complete',index<screens.indexOf(to));
  });
  document.querySelectorAll('.nav-item').forEach(el=>el.classList.toggle('active',el.dataset.go===to || (to==='decision' && el.dataset.go==='assessment')));
  document.getElementById('page-heading').textContent=titles[to][0];
  document.getElementById('page-subheading').textContent=titles[to][1];
  if(to==='decision') {const outcome=document.getElementById('decision-outcome');outcome.hidden=true;outcome.textContent='';}
  window.scrollTo({top:0,behavior:'auto'});
}
function decision(action) {
  const target=document.getElementById('decision-outcome');
  target.classList.toggle('warning',action==='continue');
  let markup='';
  if(action==='verify') markup='<h3>📞 Verify using a trusted contact</h3><p>Open your own saved contacts. Call Amir at the number you already know, or ask another family member to contact him. Do not call any number given in the suspicious message.</p><p><strong>Only act after verifying independently.</strong> This demo does not make a call or confirm identity.</p>';
  if(action==='decline') markup='<h3>✋ You chose to pause</h3><p>You do not need to send money or click anything. You can ignore the request and verify later through a known contact route.</p>';
  if(action==='continue') markup='<h3>⚠ This request is still unverified</h3><p>Continuing could expose you to loss or fraud. This demo will not open the link or make any payment. We recommend independently verifying with Amir before proceeding.</p>';
  target.innerHTML=markup;
  target.hidden=false;
  target.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function init() {
  document.getElementById('signals').innerHTML=getWarningSignals(sampleMessage).map(s=>`<div class="signal"><div class="signal-icon">${s.icon}</div><div><strong>${s.title}</strong><p>${s.detail}</p></div></div>`).join('');
  document.querySelectorAll('[data-go]').forEach(el=>el.addEventListener('click',()=>navigate(el.dataset.go)));
  document.querySelectorAll('[data-action]').forEach(el=>el.addEventListener('click',()=>decision(el.dataset.action)));
  navigate('incoming');
}
document.addEventListener('DOMContentLoaded',init);
