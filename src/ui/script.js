'use strict';
const pages = ['receive', 'understand', 'check', 'evidence', 'decide', 'support'];
const headings = {
  receive: ['Hello, Puan Salmah 👋', "You're in control. We'll help you check before you act."],
  understand: ['Understand this request', 'Analysis can highlight warning signs, but cannot verify the sender.'],
  check: ['Checking through a trusted route', 'A separate route matters more than a familiar-looking message.'],
  evidence: ['Evidence, not guesses', 'We will show what is known and what remains unresolved.'],
  decide: ['You are in control 💚', 'Choose the next step that feels right for you.'],
  support: ['Here to help 💙', 'Clear guidance, one step at a time.']
};
const REQUEST_BUDGET_MS = 40_000;
const requests = new Map();
const byId = id => document.getElementById(id);
const initialState = () => ({
  page: 'receive', setupStatus: 'idle', setupError: '', meta: null, scenario: null,
  assessmentStatus: 'idle', assessment: null, assessmentMode: null, assessmentError: '',
  recoveryStatus: 'idle', recovery: null, recoveryIncident: null, recoveryError: ''
});
const state = initialState();

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function cancelRequest(kind) {
  const request = requests.get(kind);
  if (!request) return;
  requests.delete(kind);
  clearTimeout(request.timer);
  request.controller.abort();
}

function beginRequest(kind) {
  cancelRequest(kind);
  const request = { controller: new AbortController(), timedOut: false };
  request.timer = setTimeout(() => {
    request.timedOut = true;
    request.controller.abort();
  }, REQUEST_BUDGET_MS);
  requests.set(kind, request);
  return request;
}

// Request identity also guards against responses that finish after cancellation/restart.
function isCurrent(kind, request) {
  return requests.get(kind) === request;
}

function finishRequest(kind, request) {
  clearTimeout(request.timer);
  if (isCurrent(kind, request)) requests.delete(kind);
}

class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.status = status;
  }
}

async function requestJSON(path, request, body) {
  let response;
  try {
    response = await fetch(path, {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? { Accept: 'application/json' } : {
        Accept: 'application/json', 'Content-Type': 'application/json'
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: request.controller.signal,
      cache: 'no-store'
    });
  } catch (error) {
    if (request.controller.signal.aborted) throw error;
    throw new ApiError('Could not reach the API. Check your connection and that the server is running.');
  }
  // Do not expose raw upstream error bodies, which can contain provider details.
  if (!response.ok) throw new ApiError(`The API returned HTTP ${response.status}.`, response.status);
  try {
    return await response.json();
  } catch (error) {
    if (request.controller.signal.aborted) throw error;
    throw new ApiError('The API returned an unreadable response.');
  }
}

function errorMessage(error, request, context) {
  if (request.timedOut) return `${context} timed out after 40 seconds. No result is displayed. Please retry.`;
  const detail = error instanceof ApiError ? error.message : 'An unexpected response prevented completion.';
  return `${context} failed. ${detail} No result is displayed. Please retry.`;
}

function requireResponse(valid) {
  if (!valid) throw new ApiError('The API response did not match the expected format.');
}

const isText = value => typeof value === 'string';
const hasTexts = (value, fields) => value && fields.every(field => isText(value[field]));

function validateSetup(meta, scenarios) {
  requireResponse(meta && ['qwen', 'rules'].includes(meta.engine) &&
    typeof meta.aiEnabled === 'boolean' && typeof meta.demoDataOnly === 'boolean' &&
    (isText(meta.version) || typeof meta.version === 'number'));
  const scenario = scenarios?.scenarios?.[0];
  requireResponse(Array.isArray(scenarios?.scenarios) && hasTexts(scenario, ['id', 'label']) &&
    hasTexts(scenario.message, ['sender', 'channel', 'text']) &&
    typeof scenario.message.familiarContact === 'boolean' && scenario.message.text.trim().length > 0);
  return scenario;
}

function validateAssessment(assessment, mode) {
  requireResponse(hasTexts(assessment, ['summary', 'disclaimer']) &&
    ['pause', 'no_signals'].includes(assessment.level) && ['qwen', 'rules'].includes(assessment.engine) &&
    typeof assessment.aiAvailable === 'boolean' && Array.isArray(assessment.signals) &&
    assessment.signals.every(signal => hasTexts(signal, ['id', 'icon', 'title', 'detail'])) &&
    Array.isArray(assessment.checks) && assessment.checks.every(check =>
      hasTexts(check, ['id', 'label', 'source', 'result']) &&
      ['completed', 'not_run', 'unavailable'].includes(check.status)));
  // Strict AI must never be silently presented as a rules fallback (or vice versa).
  requireResponse(assessment.engine === (mode === 'ai' ? 'qwen' : 'rules') &&
    assessment.aiAvailable === (mode === 'ai'));
}

function renderApiStatus() {
  const busy = state.setupStatus === 'loading';
  byId('init-retry').hidden = state.setupStatus !== 'error';
  byId('init-retry').disabled = busy;
  byId('api-status').classList.toggle('error-text', state.setupStatus === 'error');
  if (state.setupStatus !== 'ready') {
    byId('api-status').textContent = state.setupStatus === 'error'
      ? state.setupError : 'Loading API status and fictional sample. No assessment has run.';
    return;
  }
  const meta = state.meta;
  let analysisStatus = 'Live model availability has not been tested.';
  if (state.assessmentStatus === 'loading') {
    analysisStatus = `Assessment API request in progress (${state.assessmentMode === 'ai' ? 'live AI' : 'local rules'}).`;
  } else if (state.assessmentStatus === 'error') {
    analysisStatus = 'The last assessment request failed; no assessment result is available.';
  } else if (state.assessment) {
    analysisStatus = `Last assessment engine: ${state.assessment.engine}. AI availability reported by that response: ${state.assessment.aiAvailable ? 'yes' : 'no'}.`;
  }
  byId('api-status').textContent = `API connected · version ${meta.version} · configured engine: ${meta.engine} · AI enabled: ${meta.aiEnabled ? 'yes' : 'no'} · demo data only: ${meta.demoDataOnly ? 'yes' : 'no'}. ${analysisStatus}`;
}

function renderScenario() {
  byId('message-card').setAttribute('aria-busy', String(state.setupStatus === 'loading'));
  if (!state.scenario) {
    byId('scenario-label').textContent = state.setupStatus === 'error'
      ? 'Sample unavailable. Retry API setup above.' : 'Loading the fictional sample from the API...';
    byId('message-sender').textContent = 'Sample not loaded';
    byId('message-context').textContent = 'Sender identity is not verified';
    byId('message-avatar').textContent = '?';
    byId('message-text').textContent = state.setupStatus === 'error'
      ? 'No sample is available to assess.' : 'Loading sample message...';
    byId('evidence-scenario').textContent = 'Sample not loaded';
    return;
  }
  const { message, label } = state.scenario;
  byId('scenario-label').textContent = label;
  byId('message-sender').textContent = message.sender;
  byId('message-avatar').textContent = Array.from(message.sender)[0] || '?';
  byId('message-context').textContent = `${message.familiarContact ? 'Familiar contact' : 'Unfamiliar contact'} · ${message.channel} · Fictional sample`;
  byId('message-text').textContent = message.text;
  byId('evidence-scenario').textContent = `${label} · ${message.sender} · ${message.channel}`;
}

function assessmentStatusText() {
  if (state.assessmentStatus === 'loading') {
    return state.assessmentMode === 'ai'
      ? 'Analyzing the fictional sample with the live model. This may take up to 40 seconds. No result yet.'
      : 'Analyzing the fictional sample with local rules. No AI call is made. No result yet.';
  }
  if (state.assessmentStatus === 'error') return state.assessmentError;
  if (state.assessment) {
    return `Assessment completed using ${state.assessment.engine === 'qwen' ? 'Qwen (live model)' : 'local rules (no AI call)'}. Analysis is not identity or URL verification.`;
  }
  if (state.setupStatus === 'error') return 'No assessment has run. Retry API setup above to load the sample and engine status.';
  if (state.setupStatus !== 'ready') return 'Waiting for API status and the sample. No assessment has run.';
  return 'No assessment has run. Open Understand to analyze the fictional sample.';
}

function renderAssessment() {
  const assessment = state.assessment;
  const busy = state.assessmentStatus === 'loading';
  const failed = state.assessmentStatus === 'error';
  const statusText = assessmentStatusText();
  byId('assessment-card').setAttribute('aria-busy', String(busy));
  byId('assessment-status').textContent = statusText;
  byId('assessment-status').classList.toggle('error-text', failed || state.setupStatus === 'error');
  byId('assessment-engine').textContent = assessment
    ? (assessment.engine === 'qwen' ? 'QWEN · LIVE MODEL' : 'LOCAL RULES · NO AI CALL')
    : busy ? 'ANALYZING' : failed ? 'UNAVAILABLE' : 'NOT RUN';
  byId('assess-retry').hidden = !failed;
  byId('assess-retry').disabled = busy;
  byId('use-rules').hidden = !failed || state.assessmentMode !== 'ai';
  byId('use-rules').disabled = busy;
  byId('assessment-result').hidden = !assessment;
  byId('assessment-level').textContent = '';
  byId('assessment-title').textContent = '';
  byId('assessment-summary').textContent = '';
  byId('assessment-disclaimer').textContent = '';
  byId('signals').replaceChildren();
  if (assessment) {
    const pause = assessment.level === 'pause';
    byId('assessment-symbol').textContent = pause ? '!' : 'i';
    byId('assessment-level').textContent = pause ? 'REASONS TO PAUSE' : 'NO SIGNALS DETECTED';
    byId('assessment-title').textContent = pause ? 'Pause and verify this request' : 'No signals does not mean safe';
    byId('assessment-summary').textContent = assessment.summary;
    byId('assessment-disclaimer').textContent = assessment.disclaimer;
    for (const signal of assessment.signals) {
      const item = node('div', undefined, 'signal');
      const icon = node('span', signal.icon, 'signal-emoji');
      icon.setAttribute('aria-hidden', 'true');
      const description = node('div');
      description.append(node('strong', signal.title), node('p', signal.detail));
      item.append(icon, description);
      byId('signals').append(item);
    }
    if (!assessment.signals.length) {
      byId('signals').append(node('p', 'No warning signals were returned. This does not prove the request is safe.'));
    }
  }

  byId('analysis-check-status').textContent = assessment ? 'Completed' : busy ? 'Loading' : failed ? 'Unavailable' : 'Not run';
  byId('analysis-check-status').className = `status${assessment ? ' prepared' : failed ? ' unresolved' : ''}`;
  byId('analysis-check-detail').textContent = assessment ? assessment.summary : statusText;
  byId('evidence-status').textContent = assessment
    ? `API-provided checks · engine: ${assessment.engine}. A completed analysis is not a completed identity check.`
    : `${statusText} No check results are available.`;
  byId('evidence-assess').hidden = Boolean(assessment);
  byId('evidence-assess').textContent = busy ? 'View assessment progress' : failed ? 'View assessment and retry' : 'Assess the sample in Understand';
  byId('evidence-checks').setAttribute('aria-busy', String(busy));
  byId('evidence-checks').replaceChildren();
  byId('evidence-disclaimer').hidden = !assessment;
  byId('evidence-disclaimer').textContent = assessment ? assessment.disclaimer : '';
  if (assessment) {
    const statuses = { completed: 'Completed', not_run: 'Not run', unavailable: 'Unavailable' };
    for (const check of assessment.checks) {
      const row = node('div', undefined, 'evidence-row');
      const description = node('div');
      description.append(node('b', check.label), node('small', `Source: ${check.source}`));
      row.append(description, node('span', statuses[check.status],
        `status ${check.status === 'completed' ? 'prepared' : 'unresolved'}`), node('p', check.result));
      byId('evidence-checks').append(row);
    }
    if (!assessment.checks.length) byId('evidence-checks').append(node('p', 'The API returned no check entries. Nothing has been verified.'));
  }
  renderApiStatus();
}

async function initialize() {
  if (state.setupStatus === 'loading') return;
  const request = beginRequest('setup');
  state.setupStatus = 'loading';
  state.setupError = '';
  state.meta = null;
  state.scenario = null;
  renderScenario();
  renderAssessment();
  try {
    const [meta, scenarios] = await Promise.all([
      requestJSON('/api/meta', request), requestJSON('/api/scenarios', request)
    ]);
    if (!isCurrent('setup', request)) return;
    const scenario = validateSetup(meta, scenarios);
    state.meta = meta;
    state.scenario = scenario;
    state.setupStatus = 'ready';
    renderScenario();
    renderAssessment();
    // Never move the user or start AI if they left Understand while setup was loading.
    if (state.page === 'understand') ensureAssessment();
  } catch (error) {
    if (!isCurrent('setup', request)) return;
    state.setupStatus = 'error';
    state.setupError = errorMessage(error, request, 'API setup');
    request.controller.abort(); // Stop the other initialization request if one failed.
    renderScenario();
    renderAssessment();
  } finally {
    finishRequest('setup', request);
  }
}

function ensureAssessment() {
  if (state.setupStatus === 'ready' && state.assessmentStatus === 'idle') {
    assess(state.meta.aiEnabled ? 'ai' : 'rules');
  }
}

async function assess(mode) {
  if (state.setupStatus !== 'ready' || state.assessmentStatus === 'loading' || state.assessment) return;
  if (!['ai', 'rules'].includes(mode)) return;
  const request = beginRequest('assessment');
  state.assessmentStatus = 'loading';
  state.assessmentMode = mode;
  state.assessmentError = '';
  state.assessment = null;
  renderAssessment();
  try {
    const data = await requestJSON(`/api/assess?mode=${mode}`, request, { message: state.scenario.message });
    if (!isCurrent('assessment', request)) return;
    validateAssessment(data?.assessment, mode);
    state.assessment = data.assessment;
    state.assessmentStatus = 'success';
    renderAssessment();
  } catch (error) {
    if (!isCurrent('assessment', request)) return;
    state.assessmentStatus = 'error';
    state.assessment = null;
    state.assessmentError = mode === 'ai' && error.status === 503
      ? 'Live AI is unavailable (HTTP 503). No live assessment completed. Retry, or explicitly choose Use local rules for analysis without AI.'
      : errorMessage(error, request, mode === 'ai' ? 'Live AI analysis' : 'Local rules analysis');
    renderAssessment();
  } finally {
    finishRequest('assessment', request);
  }
}

function renderRecovery() {
  const busy = state.recoveryStatus === 'loading';
  const failed = state.recoveryStatus === 'error';
  const target = byId('recovery-content');
  target.setAttribute('aria-busy', String(busy));
  target.replaceChildren();
  target.hidden = !state.recovery;
  byId('recovery-retry').hidden = !failed;
  byId('recovery-retry').disabled = busy;
  byId('recovery-status').classList.toggle('error-text', failed);
  byId('recovery-status').textContent = busy ? 'Loading guidance for your selection. This may take up to 40 seconds.'
    : failed ? state.recoveryError : state.recovery ? 'Guidance loaded from the API for your selection.' : 'Guidance has not been requested.';
  if (!state.recovery) return;
  for (const step of [...state.recovery.steps].sort((a, b) => a.order - b.order)) {
    const row = node('div', undefined, 'recovery-step');
    const detail = node('div');
    if (step.urgent) detail.append(node('span', 'Urgent', 'status unresolved'));
    detail.append(node('h3', step.title), node('p', step.detail));
    row.append(node('span', String(step.order), 'recovery-number'), detail);
    target.append(row);
  }
  if (!state.recovery.steps.length) target.append(node('p', 'No steps were returned for this selection. Use an independently trusted support route.'));
  target.append(node('div', state.recovery.disclaimer, 'footnote'));
}

async function updateRecovery() {
  const incident = document.querySelector('input[name="incident"]:checked').value;
  if (state.recoveryStatus === 'loading' && state.recoveryIncident === incident) return;
  const request = beginRequest('recovery');
  state.recoveryStatus = 'loading';
  state.recoveryIncident = incident;
  state.recovery = null;
  state.recoveryError = '';
  renderRecovery();
  try {
    const data = await requestJSON('/api/recovery', request, { incident });
    if (!isCurrent('recovery', request)) return;
    requireResponse(data && data.incident === incident && isText(data.disclaimer) &&
      Array.isArray(data.steps) && data.steps.every(step => hasTexts(step, ['title', 'detail']) &&
        Number.isInteger(step.order) && step.order > 0 && typeof step.urgent === 'boolean'));
    state.recovery = data;
    state.recoveryStatus = 'success';
    renderRecovery();
  } catch (error) {
    if (!isCurrent('recovery', request)) return;
    state.recoveryStatus = 'error';
    state.recoveryError = errorMessage(error, request, 'Recovery guidance');
    renderRecovery();
  } finally {
    finishRequest('recovery', request);
  }
}

function showPage(page, focus = true) {
  if (!pages.includes(page)) return;
  const previous = state.page;
  state.page = page;
  pages.forEach(id => { byId(id).hidden = id !== page; });
  document.querySelectorAll('[data-step]').forEach(element => {
    element.classList.toggle('active', element.dataset.step === page);
    // Navigation alone does not mean earlier checks were completed.
    element.classList.remove('done');
    if (element.dataset.step === page) element.setAttribute('aria-current', 'step');
    else element.removeAttribute('aria-current');
  });
  document.querySelectorAll('.nav').forEach(element => {
    element.classList.toggle('active', element.dataset.go === page);
    if (element.dataset.go === page) element.setAttribute('aria-current', 'page');
    else element.removeAttribute('aria-current');
  });
  byId('page-title').textContent = headings[page][0];
  byId('page-intro').textContent = headings[page][1];
  if (page === 'understand') ensureAssessment();
  if (page === 'support' && (previous !== 'support' || state.recoveryStatus === 'idle')) updateRecovery();
  if (focus) {
    const heading = byId(`${page}-title`);
    heading.tabIndex = -1;
    heading.focus({ preventScroll: true });
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
}

function simulateCheck() {
  byId('check-status').textContent = 'Simulated · no answer';
  byId('check-status').className = 'status unresolved';
  const target = byId('simulation-result');
  target.hidden = false;
  const button = node('button', 'See evidence report →', 'btn primary');
  button.type = 'button';
  button.dataset.go = 'evidence';
  target.replaceChildren(node('strong', 'Simulation only: no confirmation obtained'),
    node('p', 'A trusted contact route would let you ask about this exact request. No call was made, no reply was received, and the request remains unverified. This local simulation does not change API check results.'), button);
  byId('family-evidence-status').textContent = 'Local simulation run · no real check';
  byId('family-evidence-detail').textContent = 'No call was made or response obtained. This simulation is not evidence of identity or legitimacy; API results above are unchanged.';
}

function setChoice(action) {
  const content = {
    verify: ['Independent verification', 'Call the claimed sender using a number you previously saved or another independently trusted route. Ask whether they sent this exact request. If you cannot reach them, ask a trusted person for help. Do not pay while the request is unverified.', 'This demo does not call anyone or confirm identity.'],
    decline: ['You chose to pause', 'Do not click the link, share details or send money. You can check later using a known contact route.', 'The app has not blocked or declined anything automatically.'],
    continue: ['The request remains unverified', 'Continuing could expose you to fraud or loss. Links remain inactive in this demo. Verify independently before any payment or sharing of details.', 'This demo does not make payments or take action on the message.']
  };
  const target = byId('choice-result');
  const choice = content[action];
  target.replaceChildren();
  target.hidden = !choice;
  if (!choice) return;
  target.append(node('h3', choice[0]), node('p', choice[1]), node('p', choice[2]));
  target.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

function resetDemo() {
  for (const kind of [...requests.keys()]) cancelRequest(kind);
  Object.assign(state, initialState());
  byId('check-status').textContent = 'Not checked';
  byId('check-status').className = 'status';
  byId('simulation-result').hidden = true;
  byId('simulation-result').replaceChildren();
  byId('family-evidence-status').textContent = 'Local simulation not run';
  byId('family-evidence-detail').textContent = 'No call was made or response obtained. The sender and request remain unverified.';
  byId('choice-result').hidden = true;
  byId('choice-result').replaceChildren();
  document.querySelector('input[name="incident"][value="clicked_link"]').checked = true;
  renderRecovery();
  showPage('receive');
  initialize();
}

function init() {
  document.addEventListener('click', event => {
    const navigation = event.target.closest('[data-go]');
    if (navigation) showPage(navigation.dataset.go);
    const choice = event.target.closest('[data-choice]');
    if (choice) setChoice(choice.dataset.choice);
  });
  byId('init-retry').addEventListener('click', initialize);
  byId('assess-retry').addEventListener('click', () => assess(state.assessmentMode));
  byId('use-rules').addEventListener('click', () => assess('rules'));
  byId('recovery-retry').addEventListener('click', updateRecovery);
  byId('simulate-check').addEventListener('click', simulateCheck);
  byId('restart').addEventListener('click', resetDemo);
  document.querySelectorAll('input[name="incident"]').forEach(radio => radio.addEventListener('change', updateRecovery));
  renderRecovery();
  showPage('receive', false);
  initialize();
}

document.addEventListener('DOMContentLoaded', init);
