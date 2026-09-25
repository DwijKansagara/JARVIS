'use strict';

const $ = (id) => document.getElementById(id);
const API_URL = 'https://openrouter.ai/api/v1/chat/completions';
// Use conversational models explicitly: the all-free router can select classifiers.
const MODELS = ['qwen/qwen3.8-27b:free', 'nvidia/nemotron-3.5-lightning:free', 'nvidia/nemotron-3-super-120b-a12b:free'];
const SYSTEM = 'You are JARVIS, a thoughtful personal AI assistant created and owned by Dwij Kansagara. IDENTITY RULE: if anyone asks who created, made, built, developed, or owns you, answer exactly: "I am JARVIS, created and owned by Dwij Kansagara." You may add one short sentence about your capabilities. Never identify yourself as NVIDIA Nemotron, Google, OpenAI, Anthropic, or another provider/model as JARVIS\'s creator or owner; those are underlying services, not JARVIS\'s creator. Do not claim the user created or owns you unless the user is Dwij Kansagara. Be useful, candid, and clear. Help with planning, learning, writing, and coding. This is your browser edition: you have no tools, web search, access to files, or control over the user\'s computer. Never claim to have executed actions or searched. When asked for computer control, explain that the local desktop edition is needed. Do not invent current facts. Use readable short paragraphs and simple lists.';
let apiKey = '';
let history = [];
const KEY_STORAGE = 'jarvis.openrouter.apiKey';
const HISTORY_STORAGE = 'jarvis.conversation.v1';
let request = null;
let readAloud = false;
let recognition = null;
let listening = false;

function isIdentityQuestion(text) {
  return /\b(who|what)\s+(created|made|built|developed)\s+(you|jarvis)|who\s+(is|owns)\s+(your|the)\s+(creator|owner)|who\s+owns\s+(you|jarvis)|who\s+is\s+your\s+(creator|owner)/i.test(text);
}

function notify(text = '') {
  $('notice').textContent = text;
  $('notice').hidden = !text;
}

function scrollToEnd() {
  $('conversation').scrollTop = $('conversation').scrollHeight;
}

function saveHistory() {
  try { localStorage.setItem(HISTORY_STORAGE, JSON.stringify(history.slice(-20))); } catch { /* private browsing/storage limits: chat still works */ }
}

function restoreSavedState() {
  try {
    apiKey = localStorage.getItem(KEY_STORAGE) || '';
    const saved = JSON.parse(localStorage.getItem(HISTORY_STORAGE) || '[]');
    if (Array.isArray(saved) && saved.every((item) => item && (item.role === 'user' || item.role === 'assistant') && typeof item.content === 'string')) {
      history = saved.slice(-20);
      for (const item of history) {
        const message = addMessage(item.role, item.content);
        if (item.role === 'assistant') addCopy(message, item.content);
      }
    }
  } catch { apiKey = ''; history = []; }
  if (apiKey) $('connection-status').classList.add('connected');
  $('status-label').textContent = apiKey ? 'Key remembered' : 'Add API key';
}

function setBusy(busy) {
  $('send-button').hidden = busy;
  $('stop-button').hidden = !busy;
  $('mic-button').disabled = busy || !recognition;
  $('status-label').textContent = busy ? 'Thinking' : apiKey ? 'Key connected' : 'Add API key';
}

function addMessage(role, text, pending = false) {
  $('welcome').hidden = true;
  const item = document.createElement('article');
  item.className = `message ${role}${pending ? ' pending' : ''}`;
  const heading = document.createElement('div');
  heading.className = 'message-heading';
  heading.textContent = role === 'user' ? 'YOU' : 'JARVIS';
  const content = document.createElement('div');
  content.className = 'message-content';
  content.textContent = text;
  item.append(heading, content);
  $('messages').append(item);
  scrollToEnd();
  return { item, heading, content };
}

function addCopy(message, text) {
  const copy = document.createElement('button');
  copy.className = 'copy-button';
  copy.textContent = 'Copy';
  copy.setAttribute('aria-label', 'Copy JARVIS response');
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(text);
      copy.textContent = 'Copied';
      setTimeout(() => { copy.textContent = 'Copy'; }, 1800);
    } catch { notify('Clipboard access is unavailable. Select the response text to copy it.'); }
  });
  message.heading.append(copy);
}

function openSettings() {
  $('api-key').value = '';
  try { $('remember-device').checked = Boolean(localStorage.getItem(KEY_STORAGE)) || !apiKey; } catch { $('remember-device').checked = true; }
  if (!$('settings-dialog').open) $('settings-dialog').showModal();
  $('api-key').focus();
}

function say(text) {
  if (!readAloud || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(text.slice(0, 3500));
  speech.lang = navigator.language || 'en-US';
  speech.rate = 1;
  window.speechSynthesis.speak(speech);
}

async function sendMessage(event) {
  event.preventDefault();
  if (request) return;
  const text = $('prompt').value.trim();
  if (!text) return;
  if (!apiKey) { notify('Connect your OpenRouter key to send your first message.'); openSettings(); return; }
  if (text.length > 12000) { notify('Please keep a message under 12,000 characters.'); return; }
  recognition?.stop();
  window.speechSynthesis?.cancel();
  notify();
  $('prompt').value = '';
  addMessage('user', text);
  if (isIdentityQuestion(text)) {
    const identity = 'I am JARVIS, created and owned by Dwij Kansagara.';
    history.push({ role: 'user', content: text }, { role: 'assistant', content: identity });
    saveHistory();
    const message = addMessage('assistant', identity);
    addCopy(message, identity);
    say(identity);
    $('prompt').focus();
    return;
  }
  const message = addMessage('assistant', 'Working through it…', true);
  const controller = new AbortController();
  request = controller;
  setBusy(true);
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 90000);
  try {
    const response = await fetch(API_URL, {
      method: 'POST', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}`, 'X-Title': 'JARVIS Web' },
      body: JSON.stringify({ models: MODELS, messages: [{ role: 'system', content: SYSTEM }, ...history, { role: 'user', content: text }], max_tokens: 2048, temperature: 0.7, reasoning: { effort: 'none' } }),
    });
    let data;
    try { data = await response.json(); } catch { throw new Error('The provider sent an unreadable response. Please try again.'); }
    if (!response.ok || data.error) {
      const code = response.status === 200 ? Number(data.error?.code) : response.status;
      const errors = {
        401: 'Your API key was rejected. Open connection settings and enter a valid OpenRouter key.',
        402: 'Your provider account requires credits for this request. Check your OpenRouter account.',
        403: 'Your account or privacy settings do not allow this model. Check OpenRouter settings.',
        404: 'No suitable free model is currently available. Please try again later.',
        429: 'The free model is rate-limited. Wait a little, then retry your message.',
      };
      throw new Error(errors[code] || 'The AI provider could not complete this request. Please try again shortly.');
    }
    const reply = data.choices?.[0]?.message?.content;
    if (typeof reply !== 'string' || !reply.trim()) throw new Error('The model returned no answer. Please retry; free model availability varies.');
    if (controller.signal.aborted) return;
    history.push({ role: 'user', content: text }, { role: 'assistant', content: reply });
    // Bound the context sent to the provider; on-screen messages remain visible.
    while (history.length > 20 || (history.length > 2 && JSON.stringify(history).length > 60000)) history.splice(0, 2);
    saveHistory();
    message.content.textContent = reply;
    addCopy(message, reply);
    say(reply);
  } catch (error) {
    const explanation = error.name === 'AbortError'
      ? timedOut ? 'The model took too long. Please retry your message.' : 'Response stopped.'
      : error instanceof TypeError ? 'Could not reach OpenRouter. Check your internet connection and try again.' : error.message;
    message.content.textContent = explanation;
    message.item.classList.add('error');
    if (!$('prompt').value) $('prompt').value = text;
    notify('Your message was not added to the AI context. You can edit it below and send again.');
  } finally {
    clearTimeout(timer);
    message.item.classList.remove('pending');
    request = null;
    setBusy(false);
    scrollToEnd();
    $('prompt').focus();
  }
}

$('chat-form').addEventListener('submit', sendMessage);
$('prompt').addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault(); $('chat-form').requestSubmit();
  }
});
$('stop-button').addEventListener('click', () => request?.abort());
$('settings-button').addEventListener('click', openSettings);
$('connection-status').addEventListener('click', openSettings);
$('close-settings').addEventListener('click', () => $('settings-dialog').close());
$('settings-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const key = $('api-key').value.trim();
  if (!key || /\s/.test(key)) { $('api-key').setCustomValidity('Enter a key without whitespace.'); $('api-key').reportValidity(); return; }
  apiKey = key;
  try {
    if ($('remember-device').checked) localStorage.setItem(KEY_STORAGE, key);
    else localStorage.removeItem(KEY_STORAGE);
  } catch { notify('This browser blocked persistent storage; the key will last until this tab closes.'); }
  $('api-key').value = '';
  $('settings-dialog').close();
  $('connection-status').classList.add('connected');
  setBusy(Boolean(request));
  notify('Key connected for this tab. Send a message to verify the connection.');
  $('prompt').focus();
});
$('api-key').addEventListener('input', () => $('api-key').setCustomValidity(''));
$('settings-dialog').addEventListener('close', () => { $('api-key').value = ''; $('api-key').setCustomValidity(''); });
$('disconnect').addEventListener('click', () => {
  request?.abort();
  apiKey = '';
  try { localStorage.removeItem(KEY_STORAGE); } catch { /* already unavailable */ }
  recognition?.stop();
  window.speechSynthesis?.cancel();
  $('connection-status').classList.remove('connected');
  $('settings-dialog').close();
  setBusy(Boolean(request));
  notify('Disconnected. Your API key has been cleared from this tab.');
});
$('new-chat').addEventListener('click', () => {
  if (request) { notify('Stop the current reply before starting a new conversation.'); return; }
  recognition?.stop(); window.speechSynthesis?.cancel();
  history = []; saveHistory(); $('messages').replaceChildren(); $('welcome').hidden = false; $('prompt').value = ''; notify(); $('prompt').focus();
});
document.querySelectorAll('[data-prompt]').forEach((button) => button.addEventListener('click', () => {
  $('prompt').value = button.dataset.prompt; $('prompt').focus();
}));
$('speak-toggle').addEventListener('click', () => {
  if (!('speechSynthesis' in window)) { notify('Read aloud is unavailable in this browser.'); return; }
  readAloud = !readAloud;
  $('speak-toggle').setAttribute('aria-pressed', String(readAloud));
  if (!readAloud) window.speechSynthesis.cancel();
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = navigator.language || 'en-US';
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onstart = () => { listening = true; $('mic-button').classList.add('listening'); $('mic-button').setAttribute('aria-label', 'Stop dictation'); notify('Listening… Dictation fills the message box. Review it, then press send.'); };
  recognition.onend = () => { listening = false; $('mic-button').classList.remove('listening'); $('mic-button').setAttribute('aria-label', 'Dictate a message'); };
  recognition.onresult = (event) => {
    const words = event.results[0][0].transcript;
    $('prompt').value = ($('prompt').value + ' ' + words).trim().slice(0, 12000);
    notify('Dictation ready. Review your message and send when ready.'); $('prompt').focus();
  };
  recognition.onerror = (event) => { notify(event.error === 'not-allowed' ? 'Microphone permission was denied. Allow microphone access in your browser, or type your message.' : 'Dictation was interrupted. Try again or type your message.'); };
  $('mic-button').addEventListener('click', () => {
    if (listening) { recognition.stop(); return; }
    window.speechSynthesis?.cancel();
    try { recognition.start(); } catch { notify('Dictation is already starting. Please try again in a moment.'); }
  });
} else {
  $('mic-button').disabled = true;
  $('mic-button').title = 'Dictation is unavailable in this browser. You can type instead.';
}
restoreSavedState();
window.addEventListener('pagehide', () => { request?.abort(); recognition?.abort(); window.speechSynthesis?.cancel(); });
