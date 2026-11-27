// QA test of image 2 by default and of the annotations starting hidden in
// media/static/media/js/zoomable_compare.js.
//
// Same approach as test_zoomable_compare_annotations.js: node's built-in test
// runner, the script in a vm context with a minimal DOM and a stub of
// OpenSeadragon. Here the gallery has thumbnails and the page can be embedded
// (iframe of the detail page, talking with postMessage).
//
// Run: node --test djangoplicity/media/tests/js/test_zoomable_compare_default_compare.js
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SCRIPT = fs.readFileSync(
  path.join(__dirname, '..', '..', 'static', 'media', 'js', 'zoomable_compare.js'), 'utf8');

// Gallery order. The main image is at one end, so a default image 2 that is
// the main one, or the first one, cannot be taken for the next/previous one.
const LAYERS = [
  { id: 'optical', title: 'Optical', label: 'Optical', is_main: true, width: 2000, height: 1000, tiles_url: '/tiles/optical/' },
  { id: 'xray', title: 'X-ray', label: 'X-ray', is_main: false, width: 2000, height: 1000, tiles_url: '/tiles/xray/' },
  { id: 'radio', title: 'Radio', label: 'Radio', is_main: false, width: 4000, height: 2000, tiles_url: '/tiles/radio/' },
];
const ANNOTATIONS = { tiles_url: 'https://storage.test/annotations/', width: 60000, height: 30000 };
const ORIGIN = 'https://site.test';

function element(attrs) {
  const listeners = {};
  const classes = {};
  const el = {
    attrs: Object.assign({}, attrs),
    hidden: false,
    disabled: false,
    textContent: '',
    value: '',
    options: [],
    classes,
    classList: {
      toggle(name, on) { classes[name] = !!on; },
      contains(name) { return !!classes[name]; },
    },
    getAttribute(name) { return name in el.attrs ? el.attrs[name] : null; },
    setAttribute(name, value) { el.attrs[name] = String(value); },
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    dispatch(type, event) { (listeners[type] || []).forEach((fn) => fn(Object.assign({ target: el }, event))); },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    scrollIntoView() {},
  };
  return el;
}

function thumb(id) {
  const el = element({ 'data-id': id });
  const badge = { textContent: '' };
  el.badge = badge;
  el.querySelector = (selector) => (selector === '.zc-badge' ? badge : null);
  el.closest = () => el;
  return el;
}

function makeItem(options) {
  return {
    source: options.tileSource,
    opacity: options.opacity,
    setOpacity(value) { this.opacity = value; },
    setPreload() {},
    getFullyLoaded() { return true; },
    addHandler() {},
    removeHandler() {},
  };
}

function isAnnotationsSource(options) {
  return typeof options.tileSource.getTileUrl === 'function';
}

// Builds the page and runs the script. Returns handles to drive it.
function load({ layers = LAYERS, search = '', embedded = false } = {}) {
  const pending = [];
  const handlers = {};
  const world = {
    items: [],
    getItemAt(i) { return this.items[i]; },
    getItemCount() { return this.items.length; },
    setItemIndex(item, index) {
      this.items.splice(this.items.indexOf(item), 1);
      this.items.splice(index, 0, item);
    },
  };
  let viewerOptions = null;
  const viewer = {
    world,
    viewport: { zoomBy() {}, applyConstraints() {}, goHome() {} },
    addOnceHandler(name, fn) { handlers[name] = fn; },
    addTiledImage(options) { pending.push(options); },
    forceRedraw() {},
  };
  function OpenSeadragon(options) { viewerOptions = options; return viewer; }
  function ZoomifyTileSource(options) { this.options = options; }
  ZoomifyTileSource.prototype.getTileUrl = function (level, x, y) {
    return this.options.tilesUrl + 'TileGroup0/' + level + '-' + x + '-' + y + '.jpg';
  };
  OpenSeadragon.ZoomifyTileSource = ZoomifyTileSource;

  const thumbs = layers.map((layer) => thumb(layer.id));
  const strip = element();
  strip.querySelectorAll = (selector) => (selector === '.zc-thumb' ? thumbs : []);
  strip.querySelector = (selector) => thumbs.find((t) => selector === '.zc-thumb[data-id="' + t.attrs['data-id'] + '"]') || null;

  const ui = {
    strip,
    thumbs,
    fade: element(),
    selectBase: element(),
    selectCompared: element(),
    slider: element(),
    fullscreen: element(),
    loading: element(),
    error: element(),
    close: element(),
    zoomIn: element(), zoomOut: element(), home: element(),
    annotations: element({
      'aria-pressed': 'false', 'data-label-on': 'Annotations ON', 'data-label-off': 'Annotations OFF' }),
  };
  ui.slider.value = '0.5';
  ui.annotations.textContent = 'Annotations OFF';
  const selectors = {
    '.zc-strip': ui.strip,
    '[data-zc-fade]': ui.fade,
    '[data-zc-select="base"]': ui.selectBase,
    '[data-zc-select="compared"]': ui.selectCompared,
    '[data-zc-opacity]': ui.slider,
    '[data-zc-fullscreen]': ui.fullscreen,
    '[data-zc-loading]': ui.loading,
    '[data-zc-error]': ui.error,
    '[data-zc-annotations]': ui.annotations,
    '[data-zc-zoom-in]': ui.zoomIn,
    '[data-zc-zoom-out]': ui.zoomOut,
    '[data-zc-home]': ui.home,
  };
  if (embedded) {
    selectors['[data-zc-close]'] = ui.close;
  }
  const scripts = {
    'zoomable-layers': { textContent: JSON.stringify(layers) },
    'zoomable-annotations': { textContent: JSON.stringify(ANNOTATIONS) },
  };
  const document = {
    readyState: 'complete',
    fullscreenEnabled: false,
    getElementById(id) { return scripts[id] || null; },
    querySelector(selector) { return selectors[selector] || null; },
    addEventListener() {},
  };
  const messageListeners = [];
  const sent = [];   // messages posted to the detail page
  const sandbox = {
    document,
    OpenSeadragon,
    URLSearchParams,
    CSS: { escape: (s) => s },
    location: { search, origin: ORIGIN },
    addEventListener(type, fn) {
      if (type === 'message') {
        messageListeners.push(fn);
      }
    },
    postMessage() {},
  };
  sandbox.window = sandbox;
  const parent = { postMessage(message) { sent.push(message); } };
  sandbox.parent = embedded ? parent : sandbox;
  vm.createContext(sandbox);
  vm.runInContext(SCRIPT, sandbox);

  return {
    ui, world, pending, sent, viewerOptions: () => viewerOptions,
    open() {
      world.items.push(makeItem({ tileSource: viewerOptions.tileSources[0], opacity: 1 }));
      handlers.open();
    },
    // A message from the detail page, as the parent window sends it
    fromParent(data) {
      messageListeners.forEach((fn) => fn({ origin: ORIGIN, source: parent, data }));
    },
    pendingImages() {
      return pending.filter((o) => !isAnnotationsSource(o)).map((o) => o.tileSource.tilesUrl);
    },
    succeedAnnotations() {
      const index = pending.findIndex(isAnnotationsSource);
      assert.notStrictEqual(index, -1, 'no pending addTiledImage for the annotations');
      const options = pending.splice(index, 1)[0];
      const item = makeItem(options);
      world.items.push(item);
      options.success({ item });
      return item;
    },
  };
}

// Image 2 as the controls show it: the select, the slider and the thumbnails
function assertCompared(page, id) {
  assert.strictEqual(page.ui.selectCompared.value, id === null ? '' : id);
  assert.strictEqual(page.ui.slider.disabled, id === null);
  page.ui.thumbs.forEach((t) => {
    const isCompared = t.attrs['data-id'] === id;
    assert.strictEqual(t.classes['is-compared'], isCompared, 'is-compared on ' + t.attrs['data-id']);
    assert.strictEqual(t.getAttribute('aria-pressed'), isCompared ? 'true' : 'false');
    if (isCompared) {
      assert.strictEqual(t.badge.textContent, '2');
    }
  });
}

test('AC5: without ?compare= image 2 is the next image of the gallery', () => {
  const page = load({ search: '?base=xray' });
  assert.strictEqual(page.ui.selectBase.value, 'xray');
  assertCompared(page, 'radio');

  // Once the viewer opens, image 2 is loaded on top of the base
  page.open();
  assert.deepStrictEqual(page.pendingImages(), ['/tiles/radio/']);
});

test('AC5: without ?base= nor ?compare= image 2 is the one after the main image', () => {
  const page = load();
  assert.strictEqual(page.ui.selectBase.value, 'optical');
  assertCompared(page, 'xray');
});

test('AC6: if the base is the last image, image 2 is the previous one', () => {
  const page = load({ search: '?base=radio' });
  assert.strictEqual(page.ui.selectBase.value, 'radio');
  assertCompared(page, 'xray');
});

test('AC7: with a single image there is no image 2 and nothing else is loaded', () => {
  const page = load({ layers: [LAYERS[0]], search: '?base=optical' });
  assert.strictEqual(page.ui.selectBase.value, 'optical');
  assertCompared(page, null);
  page.open();
  assert.deepStrictEqual(page.pendingImages(), []);
  assert.strictEqual(page.ui.error.hidden, true);
});

test('AC8: a valid ?compare= is kept as it is', () => {
  // The default for xray would be radio
  const page = load({ search: '?base=xray&compare=optical' });
  assertCompared(page, 'optical');
  page.open();
  assert.deepStrictEqual(page.pendingImages(), ['/tiles/optical/']);
});

test('AC8/P6: ?compare= equal to the base falls back to the default', () => {
  const page = load({ search: '?base=xray&compare=xray' });
  assert.strictEqual(page.ui.selectBase.value, 'xray');
  assertCompared(page, 'radio');
});

test('AC8/P6: an unknown ?compare= falls back to the default', () => {
  const page = load({ search: '?base=xray&compare=nope' });
  assertCompared(page, 'radio');
});

test('AC9: mwl:show without compare shows the default image 2', () => {
  const page = load({ search: '?base=xray&compare=optical&embed=1', embedded: true });
  page.open();
  assert.strictEqual(page.sent[0].type, 'mwl:ready');
  assertCompared(page, 'optical');

  // Reopened from the detail page in slider mode, with another band (the last)
  page.fromParent({ type: 'mwl:show', base: 'radio', compare: null });
  assert.strictEqual(page.ui.selectBase.value, 'radio');
  assertCompared(page, 'xray');
  // The detail page is told the pair on screen
  assert.deepStrictEqual(Object.assign({}, page.sent[page.sent.length - 1]),
    { type: 'mwl:pair', base: 'radio', compare: 'xray' });

  page.fromParent({ type: 'mwl:show', base: 'xray', compare: null });
  assertCompared(page, 'radio');
});

test('AC9/P6: mwl:show with a compare equal to the base or unknown shows the default', () => {
  const page = load({ search: '?base=xray&embed=1', embedded: true });
  page.open();
  page.fromParent({ type: 'mwl:show', base: 'radio', compare: 'radio' });
  assertCompared(page, 'xray');
  page.fromParent({ type: 'mwl:show', base: 'radio', compare: 'nope' });
  assertCompared(page, 'xray');
});

test('AC9: mwl:show with a valid compare is kept as it is', () => {
  const page = load({ search: '?base=xray&embed=1', embedded: true });
  page.open();
  // The default for optical would be xray
  page.fromParent({ type: 'mwl:show', base: 'optical', compare: 'radio' });
  assert.strictEqual(page.ui.selectBase.value, 'optical');
  assertCompared(page, 'radio');
});

test('AC10: the annotations start hidden and one click shows them', () => {
  const page = load({ search: '?base=xray' });
  page.open();
  const overlay = page.succeedAnnotations();
  assert.strictEqual(overlay.opacity, 0);
  assert.strictEqual(page.ui.annotations.getAttribute('aria-pressed'), 'false');
  assert.strictEqual(page.ui.annotations.textContent, 'Annotations OFF');

  page.ui.annotations.dispatch('click');
  assert.strictEqual(overlay.opacity, 1);
  assert.strictEqual(page.ui.annotations.getAttribute('aria-pressed'), 'true');
  assert.strictEqual(page.ui.annotations.textContent, 'Annotations ON');
});
