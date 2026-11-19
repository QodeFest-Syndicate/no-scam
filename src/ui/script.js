'use strict';
// WatchDog AI: synthetic, offline demonstration — no network access or real Qwen invocation.
const pages = ['receive', 'understand', 'check', 'evidence', 'decide', 'support'];
const headings = {
  receive: ['Hello, Puan Salmah 👋', "You're in control. We'll help you check before you act."],
  understand: ['Your watchdog noticed something 🐶', 'Here is why this request deserves a closer look.'],
  check: ['Checking through a trusted route', 'A separate route matters more than a familiar-looking message.'],
  evidence: ['Evidence, not guesses', 'We will show what is known and what remains unresolved.'],
  decide: ['You are in control 💚', 'Choose the next step that feels right for you.'],
  support: ['Here to help 💙', 'Clear guidance, one step at a time.']
};
const warningSigns = [
  ['⏱️', 'Urgent pressure', 'The message asks for action immediately.'],
  ['🔗', 'Unverified payment link', 'The URL is not a trusted destination we have checked.'],
  ['💳', 'Money request', 'The sender asks you to pay RM500.'],
  ['🙊', 'Discourages calling', 'The sender asks you not to check by phone.']
];
let checkSimulated = false;
function showPage(page) {
  if (!pages.includes(page)) return;
  pages.forEach(id => { document.getElementById(id).hidden = id !== page; });
  document.querySelectorAll('[data-step]').forEach(node => {
    node.classList.toggle('active', node.dataset.step === page);
    node.classList.toggle('done', pages.indexOf(node.dataset.step) < pages.indexOf(page));
  });
  document.querySelectorAll('.nav').forEach(node => node.classList.toggle('active', node.dataset.go === page));
  document.getElementById('page-title').textContent = headings[page][0];
  document.getElementById('page-intro').textContent = headings[page][1];
  if (page === 'support') updateRecovery();
  window.scrollTo({ top: 0, behavior: 'instant' });
}
function simulateCheck() {
  // Does NOT contact a family member. Even after this simulated step, identity stays unresolved.
  checkSimulated = true;
  document.getElementById('check-status').textContent = 'Simulated · no answer';
  document.getElementById('check-status').className = 'status unresolved';
  document.getElementById('simulation-result').hidden = false;
  document.getElementById('simulation-result').innerHTML = '<strong>🧪 Simulated route: awaiting confirmation</strong><p>In this example, WatchDog proposes calling Amir using his previously saved number and asking about the RM500 payment. No call was made, no family reply was received, and the request remains unverified.</p><button class="btn primary" data-go="evidence">See evidence report →</button>';
}
function setChoice(action) {
  const target = document.getElementById('choice-result');
  const content = {
    verify: '<h3>📞 Independent verification</h3><p>Open your phone contacts and call the number previously saved for Amir. Ask: “Did you ask me to send RM500 through urgent-family-pay.example?” If you cannot reach him, ask another trusted family member using a known contact route. Do not pay while the request is unverified.</p><p><b>Reminder:</b> This prototype does not call anyone or confirm identity.</p>',
    decline: '<h3>✋ You chose to pause</h3><p>Do not click the link or send money. You may contact Amir later through a known route. The app has not blocked or declined anything automatically.</p>',
    continue: '<h3>⚠️ The request remains unverified</h3><p>Continuing could expose you to fraud or loss. The original link will not open in this demo. Verify independently before any payment or sharing of details.</p>'
  };
  target.innerHTML = content[action] || '';
  target.hidden = !content[action];
  target.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}
function updateRecovery() {
  const selected = document.querySelector('input[name="incident"]:checked')?.value || 'clicked';
  const steps = {
    clicked: [
      ['Stop using the link', 'Close it and do not enter any information or download anything.'],
      ['Check what happened', 'If you downloaded a file or installed an app, avoid opening it and seek trusted device-security assistance.'],
      ['Verify separately', 'Contact the sender using a number you previously saved.']
    ],
    details: [
      ['Stop sharing information', 'Do not enter more passwords, codes, or personal details.'],
      ['Secure the affected account', 'Use the official app or website you know to change your password, review account activity and enable additional protections if available.'],
      ['Contact the real service', 'Use an independently known support route if your account or personal details may be compromised.']
    ],
    paid: [
      ['Contact your bank immediately', 'Use the number on your bank card or the bank’s official app. Explain what happened and follow their instructions.'],
      ['Seek scam response assistance', 'In Malaysia, NSRC 997 is a scam-response contact. Verify the current operating details and official guidance before presenting this in a live deployment.'],
      ['Save relevant records', 'Keep messages, transaction details and screenshots for official reporting. Do not share them with suspicious contacts.']
    ]
  };
  const target = document.getElementById('recovery-content');
  target.innerHTML = steps[selected].map(([title, detail], index) => `<div class="recovery-step"><span class="recovery-number">${index + 1}</span><div><h3>${title}</h3><p>${detail}</p></div></div>`).join('') + '<div class="footnote">Prepared general guidance only · Not a live check, guaranteed recovery, or verified current official procedure.</div>';
}
function resetDemo() {
  checkSimulated = false;
  document.getElementById('check-status').textContent = 'Not checked';
  document.getElementById('check-status').className = 'status';
  document.getElementById('simulation-result').hidden = true;
  document.getElementById('simulation-result').innerHTML = '';
  document.getElementById('family-evidence-status').textContent = 'Not completed';
  document.getElementById('family-evidence-detail').textContent = 'No response has been obtained. The request and sender remain unverified.';
  document.getElementById('choice-result').hidden = true;
  document.querySelector('input[name="incident"][value="clicked"]').checked = true;
  showPage('receive');
}
function init() {
  document.getElementById('signals').innerHTML = warningSigns.map(([icon, title, detail]) => `<div class="signal"><span class="signal-emoji">${icon}</span><div><strong>${title}</strong><p>${detail}</p></div></div>`).join('');
  document.addEventListener('click', e => {
    const nav = e.target.closest('[data-go]');
    if (nav) showPage(nav.dataset.go);
    const choice = e.target.closest('[data-choice]');
    if (choice) setChoice(choice.dataset.choice);
  });
  document.getElementById('simulate-check').addEventListener('click', simulateCheck);
  document.getElementById('restart').addEventListener('click', resetDemo);
  document.querySelectorAll('input[name="incident"]').forEach(radio => radio.addEventListener('change', updateRecovery));
  showPage('receive');
}
document.addEventListener('DOMContentLoaded', init);
