// QA test of the annotations overlay in media/static/media/js/zoomable_compare.js.
//
// No dependencies: it uses node's built-in test runner and loads the script
// in a vm context with a minimal DOM and a stub of OpenSeadragon. The stub
// ZoomifyTileSource writes tile addresses like OpenSeadragon 2.4.1
// ("TileGroupN/z-x-y.jpg").
//
// Run: node --test djangoplicity/media/tests/js/test_zoomable_compare_annotations.js
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SCRIPT = fs.readFileSync(
  path.join(__dirname, '..', '..', 'static', 'media', 'js', 'zoomable_compare.js'), 'utf8');

const LAYERS = [
  { id: 'xray', title: 'X-ray', label: 'X-ray', is_main: true, width: 2000, height: 1000, tiles_url: '/tiles/xray/' },
  { id: 'radio', title: 'Radio', label: 'Radio', is_main: false, width: 4000, height: 2000, tiles_url: '/tiles/radio/' },
];
const ANNOTATIONS = { tiles_url: 'https://storage.test/media/archives/multiwavelength/annotations_zoomable/mwl/', width: 60000, height: 30000 };

function element(attrs) {
  const listeners = {};
  const el = {
    attrs: Object.assign({}, attrs),
    hidden: false,
    disabled: false,
    textContent: '',
    value: '',
    options: [],
    classList: { toggle() {} },
    getAttribute(name) { return name in el.attrs ? el.attrs[name] : null; },
    setAttribute(name, value) { el.attrs[name] = String(value); },
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    dispatch(type) { (listeners[type] || []).forEach((fn) => fn({ target: el })); },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    scrollIntoView() {},
  };
  return el;
}

function makeItem(options) {
  return {
    source: options.tileSource,
    opacity: options.opacity,
    preload: null,
    setOpacity(value) { this.opacity = value; },
    setPreload(value) { this.preload = value; },
    getFullyLoaded() { return true; },
    addHandler() {},
    removeHandler() {},
  };
}

// Builds the page and runs the script. Returns handles to drive it.
function load({ annotations = ANNOTATIONS, search = '' } = {}) {
  const pending = [];   // addTiledImage calls not answered yet
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

  const ui = {
    strip: element(),
    fade: element(),
    selectBase: element(),
    selectCompared: element(),
    slider: element(),
    fullscreen: element(),
    loading: element(),
    error: element(),
    zoomIn: element(), zoomOut: element(), home: element(),
    annotations: annotations ? element({
      'aria-pressed': 'true', 'data-label-on': 'Annotations ON', 'data-label-off': 'Annotations OFF' }) : null,
  };
  ui.slider.value = '0.5';
  ui.error.hidden = true;
  if (ui.annotations) {
    ui.annotations.textContent = 'Annotations ON';
  }
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
  const scripts = { 'zoomable-layers': { textContent: JSON.stringify(LAYERS) } };
  if (annotations) {
    scripts['zoomable-annotations'] = { textContent: JSON.stringify(annotations) };
  }
  const document = {
    readyState: 'complete',
    fullscreenEnabled: false,
    getElementById(id) { return scripts[id] || null; },
    querySelector(selector) { return selectors[selector] || null; },
    addEventListener() {},
  };
  const sandbox = {
    document,
    OpenSeadragon,
    URLSearchParams,
    CSS: { escape: (s) => s },
    location: { search, origin: 'https://site.test' },
    addEventListener() {},
    postMessage() {},
  };
  sandbox.window = sandbox;
  sandbox.parent = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(SCRIPT, sandbox);

  return {
    ui, world, pending, viewerOptions: () => viewerOptions,
    open() {
      // OpenSeadragon opens the first tile source as the item at index 0
      world.items.push(makeItem({ tileSource: viewerOptions.tileSources[0], opacity: 1 }));
      handlers.open();
    },
    // Answers the pending addTiledImage call for this tile source.
    succeed(isAnnotations) {
      const options = takePending(pending, isAnnotations);
      const item = makeItem(options);
      world.items.push(item);
      options.success({ item });
      return item;
    },
    fail(isAnnotations) {
      takePending(pending, isAnnotations).error({});
    },
  };
}

function isAnnotationsSource(options) {
  return options.tileSource instanceof Object && typeof options.tileSource.getTileUrl === 'function';
}

function takePending(pending, isAnnotations) {
  const index = pending.findIndex((o) => isAnnotationsSource(o) === isAnnotations);
  assert.notStrictEqual(index, -1, 'no pending addTiledImage for ' + (isAnnotations ? 'annotations' : 'an image'));
  return pending.splice(index, 1)[0];
}

test('C10/AC8: only the overlay tile addresses end in .png', () => {
  const page = load();
  page.open();

  const overlay = page.pending.find(isAnnotationsSource);
  assert.ok(overlay, 'the overlay is added when the viewer opens');
  assert.strictEqual(overlay.tileSource.options.tilesUrl, ANNOTATIONS.tiles_url);
  assert.strictEqual(overlay.tileSource.options.width, 60000);
  assert.strictEqual(overlay.tileSource.options.height, 30000);
  assert.strictEqual(overlay.tileSource.getTileUrl(3, 1, 2), ANNOTATIONS.tiles_url + 'TileGroup0/3-1-2.png');
  assert.strictEqual(overlay.x, 0);
  assert.strictEqual(overlay.width, 1);
  assert.strictEqual(overlay.opacity, 1);

  // The images keep the plain Zoomify description (OpenSeadragon writes .jpg)
  assert.strictEqual(page.viewerOptions().tileSources[0].type, 'zoomifytileservice');
  assert.strictEqual(page.viewerOptions().tileSources[0].getTileUrl, undefined);
});

test('C10/AC8: the .jpg to .png change does not leak to other Zoomify sources', () => {
  const page = load();
  page.open();
  const overlay = page.pending.find(isAnnotationsSource);
  const Source = overlay.tileSource.constructor;
  const plain = new Source({ tilesUrl: '/tiles/xray/' });
  assert.strictEqual(plain.getTileUrl(3, 1, 2), '/tiles/xray/TileGroup0/3-1-2.jpg');
});

test('AC5/AC6: the overlay stays on top when image 2 is added and when the images change', () => {
  const page = load({ search: '?compare=radio' });
  page.open();

  const overlay = page.succeed(true);
  assert.strictEqual(page.world.items[page.world.items.length - 1], overlay);

  // Image 2 arrives after the overlay: placeTiledImages puts the overlay back on top
  const radio = page.succeed(false);
  assert.strictEqual(page.world.items.length, 3);
  assert.strictEqual(page.world.items[2], overlay);
  assert.strictEqual(page.world.items[1], radio);
  assert.strictEqual(overlay.opacity, 1);

  // Slider (crossfade) moves image 2 only
  page.ui.slider.value = '0.2';
  page.ui.slider.dispatch('input');
  assert.strictEqual(radio.opacity, 0.2);
  assert.strictEqual(overlay.opacity, 1);

  // Swapping image 1 and 2 with the selects
  page.ui.selectBase.value = 'radio';
  page.ui.selectBase.dispatch('change');
  assert.strictEqual(page.world.items[0], radio);
  assert.strictEqual(page.world.items[2], overlay);
  assert.strictEqual(overlay.opacity, 1);

  // Removing image 2
  page.ui.selectCompared.value = '';
  page.ui.selectCompared.dispatch('change');
  assert.strictEqual(page.world.items[page.world.items.length - 1], overlay);
  assert.strictEqual(overlay.opacity, 1);
});

test('AC7: the button is the only thing that hides and shows the overlay', () => {
  const page = load({ search: '?compare=radio' });
  page.open();
  const overlay = page.succeed(true);
  page.succeed(false);
  const button = page.ui.annotations;

  button.dispatch('click');
  assert.strictEqual(button.getAttribute('aria-pressed'), 'false');
  assert.strictEqual(button.textContent, 'Annotations OFF');
  assert.strictEqual(overlay.opacity, 0);

  // Crossfade and image changes leave it hidden
  page.ui.slider.value = '0.9';
  page.ui.slider.dispatch('input');
  page.ui.selectBase.value = 'radio';
  page.ui.selectBase.dispatch('change');
  assert.strictEqual(overlay.opacity, 0);

  button.dispatch('click');
  assert.strictEqual(button.getAttribute('aria-pressed'), 'true');
  assert.strictEqual(button.textContent, 'Annotations ON');
  assert.strictEqual(overlay.opacity, 1);
});

test('AC7: turned off before the overlay loads, it is added hidden', () => {
  const page = load();
  page.ui.annotations.dispatch('click');   // before the viewer opens
  page.open();
  const overlay = page.succeed(true);
  assert.strictEqual(overlay.opacity, 0);
  assert.strictEqual(page.ui.annotations.getAttribute('aria-pressed'), 'false');
});

test('AC11/P6: if the overlay cannot be added, the button is hidden and no error is shown', () => {
  const page = load();
  page.open();
  page.fail(true);

  assert.strictEqual(page.ui.annotations.hidden, true);
  assert.strictEqual(page.ui.error.hidden, true);
  assert.strictEqual(page.world.items.length, 1);
});

test('AC9: without annotations no overlay is added', () => {
  const page = load({ annotations: null, search: '?compare=radio' });
  page.open();

  assert.strictEqual(page.pending.filter(isAnnotationsSource).length, 0);
  page.succeed(false);
  assert.strictEqual(page.world.items.length, 2);
});
