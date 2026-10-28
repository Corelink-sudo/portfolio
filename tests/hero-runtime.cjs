// Execute the actual hero lifecycle code with deterministic media/idle events.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const code = html.split('/* ---------- Hero video: play once, then dissolve into ambient lighting ---------- */')[1]
  .split('/* ---------- Pointer-reactive hero lighting ---------- */')[0];

function setup(reduce = false) {
  const events = {}, timers = new Map(), idle = [];
  let observe, id = 0;
  const counts = { play: 0, pause: 0, load: 0, particles: 0 };
  const classes = () => {
    const set = new Set();
    return {
      add: name => set.add(name), contains: name => set.has(name),
      toggle: (name, active) => active ? set.add(name) : set.delete(name),
    };
  };
  const backdrop = { classList: classes(), style: { setProperty() {} } };
  const hero = { classList: classes() };
  const video = {
    duration: 10, currentTime: 0, ended: false, hidden: false,
    play() { counts.play++; return Promise.resolve(); },
    pause() { counts.pause++; },
    load() { counts.load++; },
    removeAttribute(name) { delete this[name]; },
    addEventListener(name, fn) { events[name] = fn; },
  };
  const document = { hidden: false, addEventListener(name, fn) { events[name] = fn; } };
  const context = vm.createContext({
    $: selector => ({ '#heroVideo': video, '.hero-media': backdrop, '#hero': hero })[selector],
    CONFIG: { heroVideo: 'test.mp4' }, reduce, document,
    setTimeout: fn => { timers.set(++id, fn); return id; },
    clearTimeout: timer => timers.delete(timer),
    window: { requestIdleCallback: true }, requestIdleCallback: fn => idle.push(fn),
    initParticles: () => counts.particles++,
    IntersectionObserver: class { constructor(fn) { observe = fn; } observe() {} },
  });
  vm.runInContext(code, context);
  return {
    counts, video, backdrop, document, timers, idle, events,
    visible: active => observe([{ isIntersecting: active }]),
    ready: () => vm.runInContext('heroReady = true; syncHeroVideo()', context),
    fade: () => { video.currentTime = 8; events.timeupdate(); },
    finish: () => events.transitionend({ propertyName: 'opacity' }),
  };
}

test('decoder and WebGL do not overlap during fade; clip cannot restart', () => {
  const s = setup();
  s.visible(true);
  assert.equal(s.counts.play, 0, 'Wait for loading curtain');
  s.ready();
  assert.equal(s.counts.play, 1);
  s.fade();
  assert.ok(s.backdrop.classList.contains('is-settled'));
  assert.equal(s.video.hidden, false, 'Keep video visible until fade finishes');
  assert.equal(s.counts.load, 0);
  assert.equal(s.idle.length, 0, 'No WebGL initialization during fade');
  s.events.transitionend({ propertyName: 'transform' });
  assert.equal(s.counts.load, 0);
  s.finish();
  assert.equal(s.video.hidden, true);
  assert.equal(s.video.src, undefined);
  assert.equal(s.counts.load, 1, 'Release media decoder after opacity transition');
  assert.equal(s.counts.particles, 0, 'Wait for idle time');
  s.idle.shift()();
  assert.equal(s.counts.particles, 1);
  s.finish();
  s.visible(false); s.visible(true);
  assert.equal(s.counts.load, 1);
  assert.equal(s.counts.play, 1, 'Never replay completed clip');
  assert.equal(s.idle.length, 0, 'Never initialize particles twice');
});

test('fallback releases decoder when transitionend is skipped', () => {
  const s = setup(); s.visible(true); s.ready(); s.fade();
  const callback = [...s.timers.values()][0];
  callback();
  assert.equal(s.video.hidden, true);
  assert.equal(s.counts.load, 1);
  assert.equal(s.timers.size, 0);
});

test('hidden tab defers particle initialization until it is visible', () => {
  const s = setup(); s.visible(true); s.ready(); s.fade();
  s.document.hidden = true; s.finish();
  assert.equal(s.idle.length, 0);
  s.document.hidden = false; s.events.visibilitychange();
  assert.equal(s.idle.length, 1);
});

test('reduced motion does not autoplay or initialize WebGL', () => {
  const s = setup(true); s.visible(true); s.ready();
  assert.equal(s.counts.play, 0);
  s.fade(); s.finish();
  assert.equal(s.idle.length, 0);
});
