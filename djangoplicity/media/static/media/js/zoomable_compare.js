// Fullscreen zoomable viewer to compare two images (templates/archives/detail_zoomable_compare.html).
//
// Image 1 is the base image. Image 2 is on top of it. The slider changes
// the opacity of image 2. A select at each end of the slider picks image 1
// and image 2, so any two images can be compared; a click on a thumbnail of
// the gallery is a shortcut to pick image 2.
//
// The page opens with ?base=<id> as image 1 (or the main image if there is
// no base). ?compare=<id> is optional and opens with that image as image 2.
//
// All images are in the same OpenSeadragon viewer, so they have the same
// zoom and position. Every image has x=0 and width 1, so images with the
// same framing are aligned, also if they have a different size in pixels.
//
// An image is loaded the first time it is needed. After that it stays in the
// viewer but hidden, so it is fast to show it again. Until its first tiles are
// on screen a loading message is shown, and an error one if they fail.
//
// With ?embed=1 the page is in an iframe of the detail page (see
// multiwavelength.js in the site). It then talks to that page with
// postMessage: "Close" hands back the image on screen, the fullscreen button
// asks the page to put the whole overlay in fullscreen, and the page can
// change the images shown without reloading the iframe.
(function () {
  'use strict';

  var ZOOM_STEP = 1.5;
  var FADE_STEP = 0.1;     // crossfade moved by one press of an arrow key

  var viewer = null;
  var viewerOpen = false;
  // The five objects below are keyed by image id.
  var layersById = {};     // Layers as the view rendered them
  var tiledImages = {};    // Tiled images already added to the viewer
  var loading = {};        // Images whose tiled image is still being added
  var shown = {};          // Images whose first tiles have been drawn
  var failed = {};         // Images whose tiles could not be loaded
  var baseId = null;      // image at the bottom (1)
  var comparedId = null;   // image on top of it (2), or null
  var embedded = false;
  var ui = {};

  // Functions to read and use the image data from the page.

  function readLayers() {
    var node = document.getElementById('zoomable-layers');
    var layers = node ? JSON.parse(node.textContent) : [];
    layers.forEach(function (layer) {
      layer.id = String(layer.id);   // data-id attributes are strings
      layersById[layer.id] = layer;
    });
    return layers;
  }

  function layerName(id) {
    var layer = layersById[id];
    return layer ? (layer.title || layer.label) : '';
  }

  function tileSource(layer) {
    return {
      type: 'zoomifytileservice',
      width: layer.width,
      height: layer.height,
      tilesUrl: layer.tiles_url
    };
  }

  // Viewer OpenSeaDragon
  function createViewer(first) {
    // Same settings as the single image zoomable page (archives/detail_zoomable.html).
    return OpenSeadragon({
      id: 'zoom',
      showNavigationControl: false,
      maxZoomPixelRatio: 3,
      imageSmoothingEnabled: false,
      animationTime: 1.2,
      tileSources: [tileSource(first)]
    });
  }

  function sliderOpacity() {
    return ui.slider ? parseFloat(ui.slider.value) : 1;
  }

  // Adds the image aligned with the others; refresh() places it once ready.
  function addTiledImage(id) {
    loading[id] = true;
    delete failed[id];
    viewer.addTiledImage({
      tileSource: tileSource(layersById[id]),
      x: 0,
      y: 0,
      width: 1,
      opacity: 0,
      success: function (event) {
        delete loading[id];
        watchFirstDraw(id, event.item);
        tiledImages[id] = event.item;
        refresh();
      },
      error: function () {
        // Not kept, so picking the image again tries once more
        delete loading[id];
        failed[id] = true;
        updateStatus();
      }
    });
  }

  // An image counts as shown once all the tiles of the first view it is
  // drawn in have arrived. Later zooms load more tiles without the message.
  function watchFirstDraw(id, item) {
    if (item.getFullyLoaded()) {
      shown[id] = true;
      return;
    }
    item.addHandler('fully-loaded-change', function onChange(event) {
      if (event.fullyLoaded) {
        shown[id] = true;
        item.removeHandler('fully-loaded-change', onChange);
        updateStatus();
      }
    });
  }

  // Loading message while image 1 or 2 has no tiles on screen yet; error
  // message if one of them failed.
  function updateStatus() {
    var visible = [baseId, comparedId].filter(function (id) { return id !== null; });
    var hasFailed = visible.some(function (id) { return failed[id]; });
    var isLoading = !hasFailed && visible.some(function (id) { return !shown[id]; });
    if (ui.loading) {
      ui.loading.hidden = !isLoading;
    }
    if (ui.error) {
      ui.error.hidden = !hasFailed;
    }
  }

  // Puts every tiled image where the current base and compared ids say:
  // the base at the bottom and opaque, the compared one on top with the
  // slider opacity, and the rest hidden and not loading tiles.
  function placeTiledImages() {
    var world = viewer.world;
    Object.keys(tiledImages).forEach(function (id) {
      var item = tiledImages[id];
      var visible = id === baseId || id === comparedId;
      item.setPreload(visible);

      var opacity = 0;
      if (id === baseId) {
        opacity = 1;
      } else if (id === comparedId) {
        opacity = sliderOpacity();
      }
      item.setOpacity(opacity);
    });
    if (tiledImages[baseId]) {
      world.setItemIndex(tiledImages[baseId], 0);
    }
    if (comparedId !== null && tiledImages[comparedId]) {
      world.setItemIndex(tiledImages[comparedId], world.getItemCount() - 1);
    }
    viewer.forceRedraw();
  }

  // CROSSFADE CONTROLS

  // Brings the viewer and the controls in line with baseId and comparedId.
  function refresh() {
    updateControls();
    updateStatus();
    if (!viewerOpen) {
      return;   // the 'open' handler calls refresh() again
    }
    [baseId, comparedId].forEach(function (id) {
      if (id !== null && !tiledImages[id] && !loading[id]) {
        addTiledImage(id);
      }
    });
    placeTiledImages();
  }

  // A new image 2 starts half faded in, as on the first pick: kept at the
  // previous position, a slider left near image 1 would hide it completely.
  function setCompared(id) {
    if (id !== null && id !== comparedId && ui.slider) {
      ui.slider.value = 0.5;
    }
    comparedId = id;
    refresh();
    revealThumb(comparedId);
  }

  // Shows another pair without reloading, when the detail page asks.
  function setPair(base, compared) {
    if (!layersById[base]) {
      return;
    }
    baseId = base;
    setCompared(compared && compared !== base && layersById[compared] ? compared : null);
    revealThumb(baseId);
  }

  // The new image 1, picked in its select. If it was image 2, the old
  // image 1 takes its place, so the pair is kept.
  function setBase(id) {
    if (id === baseId) {
      return;
    }
    if (id === comparedId) {
      comparedId = baseId;
    }
    baseId = id;
    refresh();
    revealThumb(baseId);
  }

  // Thumbnails, selects and slider follow the base and compared images.
  function updateControls() {
    ui.strip.querySelectorAll('.zc-thumb').forEach(function (thumb) {
      var id = thumb.getAttribute('data-id');
      var isBase = id === baseId;
      var isCompared = id === comparedId;
      thumb.classList.toggle('is-base', isBase);
      thumb.classList.toggle('is-compared', isCompared);
      thumb.setAttribute('aria-pressed', isCompared ? 'true' : 'false');

      var badge = '';
      if (isBase) {
        badge = '1';
      } else if (isCompared) {
        badge = '2';
      }
      thumb.querySelector('.zc-badge').textContent = badge;
    });

    if (ui.fade) {
      ui.selectBase.value = baseId;
      ui.selectCompared.value = comparedId === null ? '' : comparedId;
      // An image cannot be 1 and 2 at once
      Array.prototype.forEach.call(ui.selectCompared.options, function (option) {
        option.disabled = option.value === baseId;
      });
      ui.slider.disabled = comparedId === null;
    }

    // So the detail page shows this pair when the browser's back button
    // closes the overlay instead of the Close button.
    if (embedded) {
      postToParent({ type: 'mwl:pair', base: baseId, compare: comparedId });
    }
  }

  // Scrolls the gallery, if needed, so that the thumbnail of this image is visible.
  function revealThumb(id) {
    var thumb = id === null ? null : ui.strip.querySelector('.zc-thumb[data-id="' + CSS.escape(id) + '"]');
    if (thumb) {
      thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    }
  }

  // ZOOMABLE VIEWER CONTROLS

  function bindGalleryEvents() {
    // Clicking a thumbnail makes it image 2, unless it is image 1; clicking
    // image 2 again removes it.
    ui.strip.addEventListener('click', function (event) {
      var thumb = event.target.closest('.zc-thumb');
      if (!thumb) {
        return;
      }
      var id = thumb.getAttribute('data-id');
      if (id !== baseId) {
        setCompared(id === comparedId ? null : id);
      }
    });

    // A vertical mouse wheel scrolls the gallery sideways.
    ui.strip.addEventListener('wheel', function (event) {
      var overflows = ui.strip.scrollWidth > ui.strip.clientWidth;
      if (overflows && Math.abs(event.deltaY) > Math.abs(event.deltaX)) {
        ui.strip.scrollLeft += event.deltaY;
        event.preventDefault();
      }
    }, { passive: false });
  }

  function applySliderOpacity() {
    if (comparedId !== null && tiledImages[comparedId]) {
      tiledImages[comparedId].setOpacity(sliderOpacity());
    }
  }

  function bindSlider() {
    if (!ui.slider) {
      return;
    }
    ui.slider.addEventListener('input', applySliderOpacity);

    // While two images are compared, the left and right arrows move the
    // crossfade (towards image 1 and image 2) instead of panning the image,
    // which is what OpenSeadragon does with them. Caught on the way down, so
    // before OpenSeadragon's own handler; the slider and the selects keep
    // their own keys.
    window.addEventListener('keydown', function (event) {
      var step = event.key === 'ArrowRight' ? FADE_STEP : (event.key === 'ArrowLeft' ? -FADE_STEP : 0);
      var tag = (event.target.tagName || '').toLowerCase();
      if (!step || comparedId === null || tag === 'input' || tag === 'select' ||
          event.metaKey || event.ctrlKey || event.altKey) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      ui.slider.value = Math.min(1, Math.max(0, sliderOpacity() + step));
      applySliderOpacity();
    }, true);
  }

  function bindSelects() {
    if (!ui.fade) {
      return;
    }
    ui.selectBase.addEventListener('change', function () {
      setBase(ui.selectBase.value);
    });
    ui.selectCompared.addEventListener('change', function () {
      setCompared(ui.selectCompared.value || null);
    });
  }

  function bindZoomButtons() {
    function zoomBy(factor) {
      viewer.viewport.zoomBy(factor);
      viewer.viewport.applyConstraints();
    }
    onClick('[data-zc-zoom-in]', function () { zoomBy(ZOOM_STEP); });
    onClick('[data-zc-zoom-out]', function () { zoomBy(1 / ZOOM_STEP); });
    onClick('[data-zc-home]', function () { viewer.viewport.goHome(); });

    // + and - zoom like the buttons wherever the focus is (OpenSeadragon only
    // listens to them on its canvas). = and _ are the same keys unshifted.
    // Caught on the way down so OpenSeadragon does not zoom a second time;
    // Ctrl/Cmd + and - are left to the browser's own zoom.
    var KEY_FACTORS = { '+': ZOOM_STEP, '=': ZOOM_STEP, '-': 1 / ZOOM_STEP, '_': 1 / ZOOM_STEP };

    window.addEventListener('keydown', function (event) {
      var factor = KEY_FACTORS[event.key];
      if (!factor) {
        return;
      }
      if (event.metaKey || event.ctrlKey || event.altKey) {
        return;
      }
      if (event.target.closest('input, select, textarea')) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      zoomBy(factor);
    }, true);
  }

  // The icon and the label say what the button does next: enter or exit.
  function showFullscreenState(active) {
    var button = ui.fullscreen;
    var label = button.getAttribute(active ? 'data-label-exit' : 'data-label-enter');
    button.classList.toggle('is-fullscreen', active);
    button.setAttribute('aria-label', label);
    button.setAttribute('title', label);
  }

  // Embedded, the detail page puts its whole overlay in fullscreen and tells
  // the state back (see bindParentMessages); alone, this page does it itself.
  function bindFullscreenButton() {
    if (!document.fullscreenEnabled) {
      ui.fullscreen.hidden = true;
      return;
    }
    onClick('[data-zc-fullscreen]', function () {
      if (embedded) {
        postToParent({ type: 'mwl:fullscreen' });
      } else if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen();
      }
    });
    if (!embedded) {
      document.addEventListener('fullscreenchange', function () {
        showFullscreenState(!!document.fullscreenElement);
      });
    }
  }

  // EMBEDDED IN THE DETAIL PAGE

  function postToParent(message) {
    window.parent.postMessage(message, window.location.origin);
  }

  function close() {
    postToParent({ type: 'mwl:close', base: baseId, compare: comparedId });
  }

  function bindParentMessages() {
    onClick('[data-zc-close]', close);
    // In fullscreen the browser takes Escape for itself and leaves it
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        close();
      }
    });
    window.addEventListener('message', function (event) {
      if (event.origin !== window.location.origin || event.source !== window.parent || !event.data) {
        return;
      }
      if (event.data.type === 'mwl:show') {
        setPair(String(event.data.base), event.data.compare ? String(event.data.compare) : null);
      } else if (event.data.type === 'mwl:fullscreen-state') {
        showFullscreenState(!!event.data.active);
      }
    });
  }

  // Utility for controls
  function onClick(selector, handler) {
    document.querySelector(selector).addEventListener('click', handler);
  }

  // Utility to read an image id from the query params (?base= or ?compare=).
  // Returns null if the id is not one of the images of the page.
  function idFromUrl(name) {
    var id = new URLSearchParams(window.location.search).get(name);
    return id && layersById[id] ? id : null;
  }

  function init() {
    var layers = readLayers();
    var main = layers.filter(function (layer) { return layer.is_main; })[0] || layers[0];
    if (!main) {
      return;
    }

    ui.strip = document.querySelector('.zc-strip');
    ui.fade = document.querySelector('[data-zc-fade]');
    ui.selectBase = document.querySelector('[data-zc-select="base"]');
    ui.selectCompared = document.querySelector('[data-zc-select="compared"]');
    ui.slider = document.querySelector('[data-zc-opacity]');
    ui.fullscreen = document.querySelector('[data-zc-fullscreen]');
    ui.loading = document.querySelector('[data-zc-loading]');
    ui.error = document.querySelector('[data-zc-error]');
    embedded = window.parent !== window && !!document.querySelector('[data-zc-close]');

    baseId = idFromUrl('base') || main.id;
    var compared = idFromUrl('compare');
    comparedId = compared !== baseId ? compared : null;

    viewer = createViewer(layersById[baseId]);
    var firstId = baseId;
    viewer.addOnceHandler('open', function () {
      viewerOpen = true;
      tiledImages[firstId] = viewer.world.getItemAt(0);
      watchFirstDraw(firstId, tiledImages[firstId]);
      refresh();
    });
    viewer.addOnceHandler('open-failed', function () {
      failed[firstId] = true;
      updateStatus();
    });

    bindGalleryEvents();
    bindSlider();
    bindSelects();
    bindZoomButtons();
    bindFullscreenButton();
    if (embedded) {
      bindParentMessages();
      postToParent({ type: 'mwl:ready' });
    }
    updateControls();
    updateStatus();
    revealThumb(baseId);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
