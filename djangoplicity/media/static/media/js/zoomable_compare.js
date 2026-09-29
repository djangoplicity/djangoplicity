// Fullscreen zoomable viewer to compare two images (templates/archives/detail_zoomable_compare.html).
//
// Image 1 is the base image. Image 2 is on top of it. The slider changes
// the opacity of image 2. The user picks image 2 in the gallery. The swap
// button changes image 1 and image 2, so the user can compare any two images.
//
// The page opens with ?base=<id> as image 1 (or the main image if there is
// no base). ?compare=<id> is optional and opens with that image as image 2.
//
// All images are in the same OpenSeadragon viewer, so they have the same
// zoom and position. Every image has x=0 and width 1, so images with the
// same framing are aligned, also if they have a different size in pixels.
//
// An image is loaded the first time it is needed. After that it stays in the
// viewer but hidden, so it is fast to show it again.
(function () {
  'use strict';

  var ZOOM_STEP = 1.5;

  var viewer = null;
  var viewerOpen = false;
  // The three objects below are keyed by image id.
  var layersById = {};     // Layers as the view rendered them
  var tiledImages = {};    // Tiled images already added to the viewer
  var loading = {};        // Images whose tiled image is still being added
  var baseId = null;      // image at the bottom (1)
  var comparedId = null;   // image on top of it (2), or null
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
    return layer ? (layer.label || layer.title) : '';
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
    viewer.addTiledImage({
      tileSource: tileSource(layersById[id]),
      x: 0,
      y: 0,
      width: 1,
      opacity: 0,
      success: function (event) {
        delete loading[id];
        tiledImages[id] = event.item;
        refresh();
      },
      error: function () {
        delete loading[id];
      }
    });
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
  }

  // CROSSFADE CONTROLS

  // Brings the viewer and the controls in line with baseId and comparedId.
  function refresh() {
    updateControls();
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

  function setCompared(id) {
    comparedId = id;
    refresh();
    revealThumb(comparedId);
  }

  // The compared image becomes the base and the other way round. The slider
  // is mirrored so that what is on screen does not change.
  function swap() {
    if (comparedId === null) {
      return;
    }
    var id = baseId;
    baseId = comparedId;
    comparedId = id;
    if (ui.slider) {
      ui.slider.value = 1 - sliderOpacity();
    }
    ui.swap.classList.toggle('is-swapped');
    refresh();
    revealThumb(baseId);
  }

  // Thumbnails, slider labels and hint follow the base and compared images.
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
      ui.fade.hidden = comparedId === null;
      ui.hint.hidden = comparedId !== null;
      ui.baseName.textContent = layerName(baseId);
      ui.comparedName.textContent = layerName(comparedId);
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
    // Clicking a thumbnail makes it the compared image, unless it is the base.
    ui.strip.addEventListener('click', function (event) {
      var thumb = event.target.closest('.zc-thumb');
      if (!thumb || thumb.getAttribute('data-id') === baseId) {
        return;
      }
      var id = thumb.getAttribute('data-id');
      setCompared(id === comparedId ? null : id);
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

  function bindSlider() {
    if (!ui.slider) {
      return;
    }
    ui.slider.addEventListener('input', function () {
      if (comparedId !== null && tiledImages[comparedId]) {
        tiledImages[comparedId].setOpacity(sliderOpacity());
      }
    });
    onClick('[data-zc-swap]', swap);
  }

  function bindZoomButtons() {
    function zoomBy(factor) {
      viewer.viewport.zoomBy(factor);
      viewer.viewport.applyConstraints();
    }
    onClick('[data-zc-zoom-in]', function () { zoomBy(ZOOM_STEP); });
    onClick('[data-zc-zoom-out]', function () { zoomBy(1 / ZOOM_STEP); });
    onClick('[data-zc-home]', function () { viewer.viewport.goHome(); });
  }

  function bindFullscreenButton() {
    if (!document.fullscreenEnabled) {
      document.querySelector('[data-zc-fullscreen]').hidden = true;
      return;
    }
    onClick('[data-zc-fullscreen]', function () {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen();
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
    ui.baseName = document.querySelector('[data-zc-base-name]');
    ui.comparedName = document.querySelector('[data-zc-fade-name]');
    ui.hint = document.querySelector('[data-zc-hint]');
    ui.slider = document.querySelector('[data-zc-opacity]');
    ui.swap = document.querySelector('[data-zc-swap]');

    baseId = idFromUrl('base') || main.id;
    var compared = idFromUrl('compare');
    comparedId = compared !== baseId ? compared : null;

    viewer = createViewer(layersById[baseId]);
    viewer.addOnceHandler('open', function () {
      viewerOpen = true;
      tiledImages[baseId] = viewer.world.getItemAt(0);
      refresh();
    });

    bindGalleryEvents();
    bindSlider();
    bindZoomButtons();
    bindFullscreenButton();
    updateControls();
    revealThumb(baseId);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
