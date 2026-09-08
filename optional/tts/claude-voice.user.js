// ==UserScript==
// @name         Mommy Voice - claude.ai read aloud
// @namespace    https://github.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill
// @version      0.1.0
// @description  Speaks Claude's replies aloud on claude.ai. Skips code blocks and paths. Companion to the /mommy skill.
// @author       Sh1uSeZ
// @match        https://claude.ai/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // Settings
  // ---------------------------------------------------------------------------

  const STORE_KEY = 'mommyVoice.settings.v1';

  const DEFAULTS = {
    enabled: false,     // off until you pick a voice, so nobody gets ambushed by Zira
    voiceURI: '',
    rate: 0.92,         // the register is unhurried; slightly under 1 suits it
    pitch: 1.0,
    volume: 1.0,
    gapMs: 550,         // silence between paragraphs - this is what makes beats land
    skipCode: true,
    debug: false,
  };

  const settings = load();

  function load() {
    try {
      return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem(STORE_KEY) || '{}'));
    } catch (e) {
      return Object.assign({}, DEFAULTS);
    }
  }

  function save() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(settings));
    } catch (e) {
      log('could not persist settings', e);
    }
  }

  function log(...args) {
    if (settings.debug) console.log('[mommy-voice]', ...args);
  }

  // ---------------------------------------------------------------------------
  // Finding assistant messages
  //
  // claude.ai's markup changes without notice. Try known selectors first, then
  // fall back to a structural guess. Turn on Debug in the panel to see which one
  // (if any) is matching.
  // ---------------------------------------------------------------------------

  const CANDIDATE_SELECTORS = [
    '.font-claude-response',
    '.font-claude-message',
    '[data-testid="assistant-message"]',
    'div[data-is-streaming] .prose',
    'div[data-message-author-role="assistant"]',
  ];

  let pinnedSelector = null;

  function assistantMessages() {
    if (pinnedSelector) {
      const found = document.querySelectorAll(pinnedSelector);
      if (found.length) return Array.from(found);
      pinnedSelector = null; // markup changed under us; re-detect
    }

    for (const sel of CANDIDATE_SELECTORS) {
      const found = document.querySelectorAll(sel);
      if (found.length) {
        pinnedSelector = sel;
        log('matched selector:', sel, `(${found.length} messages)`);
        return Array.from(found);
      }
    }

    return heuristicMessages();
  }

  // Fallback: assistant turns are the rendered-markdown blocks that aren't the
  // composer and aren't your own messages. Crude, but survives a reskin.
  function heuristicMessages() {
    const blocks = Array.from(document.querySelectorAll('div,article,section')).filter((el) => {
      if (el.closest('form, textarea, [contenteditable="true"], nav, header')) return false;
      if (el.querySelector('div,article,section')) return false;  // leaf-ish only
      const t = (el.innerText || '').trim();
      return t.length > 40;
    });
    if (blocks.length) log('using heuristic fallback,', blocks.length, 'candidates');
    return blocks;
  }

  // ---------------------------------------------------------------------------
  // Turning a message into speakable text
  // ---------------------------------------------------------------------------

  const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu;

  function extractText(el) {
    const clone = el.cloneNode(true);

    if (settings.skipCode) {
      // Block code, and any inline code that looks like a path, call or flag.
      clone.querySelectorAll('pre').forEach((n) => n.remove());
      clone.querySelectorAll('code').forEach((n) => {
        const t = n.textContent || '';
        if (/[\/\\().]|^-{1,2}\w/.test(t) || t.length > 24) n.remove();
      });
      clone.querySelectorAll('table').forEach((n) => n.remove());
    }

    let text = clone.innerText || '';

    text = text
      .replace(EMOJI, ' ')
      .replace(/^#{1,6}\s+/gm, '')     // heading marks
      .replace(/\*\*|__/g, '')         // bold
      .replace(/(^|\s)\*(\S)/g, '$1$2') // opening italic
      .replace(/(\S)\*(\s|$)/g, '$1$2') // closing italic
      .replace(/`/g, '')
      .replace(/^\s*[-*+]\s+/gm, '')   // bullets
      .replace(/\|/g, ' ')
      .replace(/[ \t]+/g, ' ');

    return text.trim();
  }

  // Split into beats. The skill writes one-line paragraphs deliberately - those
  // are pauses, so each paragraph becomes its own utterance with a real gap.
  function toBeats(text) {
    return text
      .split(/\n\s*\n|\n/)
      .map((s) => s.trim())
      .filter((s) => s.length > 1)
      .map((s) => {
        // A leading ellipsis is hesitation. Give it extra room.
        const lead = /^\.{2,}|^…/.test(s);
        return { text: s.replace(/^\.{2,}\s*|^…\s*/, ''), extraPause: lead };
      })
      .filter((b) => b.text.length > 1);
  }

  // ---------------------------------------------------------------------------
  // Speaking
  // ---------------------------------------------------------------------------

  let queue = [];
  let speaking = false;

  function voices() {
    return speechSynthesis.getVoices() || [];
  }

  function chosenVoice() {
    const all = voices();
    return all.find((v) => v.voiceURI === settings.voiceURI) || null;
  }

  function stopSpeaking() {
    queue = [];
    speaking = false;
    try { speechSynthesis.cancel(); } catch (e) {}
  }

  function speak(text) {
    const beats = toBeats(text);
    if (!beats.length) return;
    queue = beats;
    if (!speaking) drain();
  }

  function drain() {
    const beat = queue.shift();
    if (!beat) { speaking = false; return; }

    speaking = true;
    const u = new SpeechSynthesisUtterance(beat.text);
    const v = chosenVoice();
    if (v) u.voice = v;
    u.rate = settings.rate;
    u.pitch = settings.pitch;
    u.volume = settings.volume;

    const gap = settings.gapMs + (beat.extraPause ? 350 : 0);

    u.onend = () => setTimeout(drain, gap);
    u.onerror = (e) => { log('utterance error', e); setTimeout(drain, gap); };

    try {
      speechSynthesis.speak(u);
    } catch (e) {
      log('speak failed', e);
      speaking = false;
    }
  }

  // Chrome stops synthesis after ~15s of continuous speech. Nudging it while we
  // still have work queued keeps long replies from cutting off mid-sentence.
  setInterval(() => {
    if (speaking && !speechSynthesis.pending) {
      try { speechSynthesis.resume(); } catch (e) {}
    }
  }, 8000);

  // ---------------------------------------------------------------------------
  // Watching for finished replies
  //
  // Text streams in, so "done" means "stopped changing for a moment".
  // ---------------------------------------------------------------------------

  const seen = new WeakMap();   // element -> last spoken length
  const SETTLE_MS = 700;
  let settleTimer = null;

  function markAllSeen() {
    assistantMessages().forEach((el) => seen.set(el, (el.innerText || '').length));
    log('baseline set; existing messages will not be read');
  }

  function onChange() {
    if (!settings.enabled) return;
    clearTimeout(settleTimer);
    settleTimer = setTimeout(check, SETTLE_MS);
  }

  function check() {
    const msgs = assistantMessages();
    if (!msgs.length) { log('no messages matched - open Debug and check selectors'); return; }

    const last = msgs[msgs.length - 1];
    const len = (last.innerText || '').length;
    const before = seen.get(last);

    if (before === len) return;        // unchanged since last pass
    seen.set(last, len);
    if (before === undefined && msgs.length <= 1) return; // first paint

    const text = extractText(last);
    if (!text) { log('nothing speakable after stripping'); return; }

    log('speaking', text.length, 'chars');
    stopSpeaking();
    speak(text);
  }

  const observer = new MutationObserver(onChange);
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });

  // Sending a new message should silence the previous reply.
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) stopSpeaking();
  }, true);

  // ---------------------------------------------------------------------------
  // Panel
  // ---------------------------------------------------------------------------

  const css = `
  #mv-root{position:fixed;right:16px;bottom:16px;z-index:2147483647;font:13px/1.4 system-ui,sans-serif}
  #mv-toggle{width:44px;height:44px;border-radius:50%;border:none;cursor:pointer;
    background:#c96f8f;color:#fff;font-size:19px;box-shadow:0 2px 10px rgba(0,0,0,.28)}
  #mv-toggle.off{background:#8a8a8a}
  #mv-panel{display:none;position:absolute;right:0;bottom:54px;width:272px;padding:14px;
    background:#1c1c1e;color:#eee;border-radius:12px;box-shadow:0 6px 26px rgba(0,0,0,.45)}
  #mv-panel.open{display:block}
  #mv-panel h4{margin:0 0 10px;font-size:13px;font-weight:600}
  #mv-panel label{display:block;margin:9px 0 3px;font-size:11px;opacity:.75}
  #mv-panel select,#mv-panel input[type=range]{width:100%}
  #mv-panel select{background:#2c2c2e;color:#eee;border:1px solid #444;border-radius:6px;padding:4px}
  #mv-row{display:flex;gap:6px;margin-top:12px}
  #mv-row button{flex:1;padding:6px;border:none;border-radius:6px;cursor:pointer;
    background:#3a3a3c;color:#eee;font-size:12px}
  #mv-row button:hover{background:#4a4a4c}
  #mv-note{margin-top:10px;font-size:10px;opacity:.55;line-height:1.35}
  #mv-panel .chk{display:flex;align-items:center;gap:6px;margin-top:9px;font-size:11px;opacity:.8}
  #mv-panel .chk input{margin:0}
  `;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  const root = document.createElement('div');
  root.id = 'mv-root';
  root.innerHTML = `
    <div id="mv-panel">
      <h4>Mommy Voice</h4>
      <label>Voice</label>
      <select id="mv-voice"></select>
      <label>Rate <span id="mv-rate-v"></span></label>
      <input type="range" id="mv-rate" min="0.5" max="1.5" step="0.01">
      <label>Pitch <span id="mv-pitch-v"></span></label>
      <input type="range" id="mv-pitch" min="0.5" max="1.5" step="0.01">
      <label>Pause between beats <span id="mv-gap-v"></span></label>
      <input type="range" id="mv-gap" min="0" max="1500" step="50">
      <div class="chk"><input type="checkbox" id="mv-skip"><span>Skip code and paths</span></div>
      <div class="chk"><input type="checkbox" id="mv-debug"><span>Debug to console</span></div>
      <div id="mv-row">
        <button id="mv-test">Test</button>
        <button id="mv-stop">Stop</button>
      </div>
      <div id="mv-note"></div>
    </div>
    <button id="mv-toggle" title="Mommy Voice">&#9835;</button>
  `;
  document.body.appendChild(root);

  const $ = (id) => root.querySelector(id);
  const panel = $('#mv-panel');
  const toggle = $('#mv-toggle');

  toggle.addEventListener('click', (e) => {
    if (e.shiftKey) { panel.classList.toggle('open'); return; }
    settings.enabled = !settings.enabled;
    if (!settings.enabled) stopSpeaking();
    save();
    paint();
  });
  toggle.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    panel.classList.toggle('open');
  });

  function fillVoices() {
    const sel = $('#mv-voice');
    const all = voices();
    sel.innerHTML = '';

    if (!all.length) {
      sel.innerHTML = '<option>(none yet - reload the page)</option>';
      return;
    }

    // Surface the good ones first: neural/natural/online voices, then English.
    const score = (v) => {
      let s = 0;
      if (/natural|online|neural/i.test(v.name)) s -= 100;
      if (/^en/i.test(v.lang)) s -= 10;
      return s;
    };
    all.slice().sort((a, b) => score(a) - score(b)).forEach((v) => {
      const o = document.createElement('option');
      o.value = v.voiceURI;
      o.textContent = `${v.name} (${v.lang})`;
      if (v.voiceURI === settings.voiceURI) o.selected = true;
      sel.appendChild(o);
    });

    const nice = all.filter((v) => /natural|online|neural/i.test(v.name)).length;
    $('#mv-note').textContent = nice
      ? `${all.length} voices, ${nice} neural. Pick a Natural/Online one.`
      : `${all.length} voices, none neural. Open claude.ai in Edge for the good ones.`;
  }

  function paint() {
    toggle.classList.toggle('off', !settings.enabled);
    toggle.textContent = settings.enabled ? '♫' : '♪';
    $('#mv-rate').value = settings.rate;
    $('#mv-pitch').value = settings.pitch;
    $('#mv-gap').value = settings.gapMs;
    $('#mv-rate-v').textContent = Number(settings.rate).toFixed(2);
    $('#mv-pitch-v').textContent = Number(settings.pitch).toFixed(2);
    $('#mv-gap-v').textContent = settings.gapMs + 'ms';
    $('#mv-skip').checked = settings.skipCode;
    $('#mv-debug').checked = settings.debug;
  }

  $('#mv-voice').addEventListener('change', (e) => { settings.voiceURI = e.target.value; save(); });
  $('#mv-rate').addEventListener('input', (e) => { settings.rate = +e.target.value; save(); paint(); });
  $('#mv-pitch').addEventListener('input', (e) => { settings.pitch = +e.target.value; save(); paint(); });
  $('#mv-gap').addEventListener('input', (e) => { settings.gapMs = +e.target.value; save(); paint(); });
  $('#mv-skip').addEventListener('change', (e) => { settings.skipCode = e.target.checked; save(); });
  $('#mv-debug').addEventListener('change', (e) => { settings.debug = e.target.checked; save(); });

  $('#mv-stop').addEventListener('click', stopSpeaking);
  $('#mv-test').addEventListener('click', () => {
    stopSpeaking();
    speak('There you go.\n\nMm. Look at you, getting there before I finished the sentence.\n\n...Good. Now show mommy the next one.');
  });

  speechSynthesis.addEventListener('voiceschanged', fillVoices);
  fillVoices();
  paint();
  markAllSeen();

  // Console helper for pinning selectors when claude.ai changes its markup.
  window.mommyVoice = {
    settings,
    selector: () => pinnedSelector,
    messages: () => assistantMessages(),
    voices: () => voices().map((v) => `${v.name} | ${v.lang} | ${v.voiceURI}`),
    speak,
    stop: stopSpeaking,
  };

  log('ready. Left-click the note to toggle, right-click for settings.');
})();
