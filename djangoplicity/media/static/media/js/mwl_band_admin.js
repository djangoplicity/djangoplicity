// Multiwavelength image admin: preview of the derived band.
//
// The editor types a frequency in hertz and the band of the spectrum follows
// from it, but the band is a property of the model, so it is only known once
// the row has been saved. This fills the read-only Band column in as the
// editor types, using the bounds the change form renders into
// #mwl-band-cuts from WAVELENGTH_BAND_CUTS.
(function () {
  'use strict';

  var SPEED_OF_LIGHT = 299792458;
  var cuts = null;   // [[lowerHz, label], ...] highest energy first

  function loadCuts() {
    var node = document.getElementById('mwl-band-cuts');
    if (!node) {
      return null;
    }
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      return null;
    }
  }

  function bandFor(hz) {
    for (var i = 0; i < cuts.length; i++) {
      if (hz >= cuts[i][0]) {
        return cuts[i][1];
      }
    }
    return cuts[cuts.length - 1][1];
  }

  // "500 nm", "1 mm", "10 cm"...
  function wavelengthLabel(hz) {
    var metres = SPEED_OF_LIGHT / hz;
    var units = [
      { factor: 1, name: 'm' },
      { factor: 1e-2, name: 'cm' },
      { factor: 1e-3, name: 'mm' },
      { factor: 1e-6, name: 'µm' },
      { factor: 1e-9, name: 'nm' },
      { factor: 1e-12, name: 'pm' }
    ];
    for (var i = 0; i < units.length; i++) {
      var value = metres / units[i].factor;
      if (value >= 1) {
        return (Math.round(value * 10) / 10) + ' ' + units[i].name;
      }
    }
    return metres.toExponential(1) + ' m';
  }

  function update(input) {
    var row = input.closest ? input.closest('tr') : null;
    var cell = row ? row.querySelector('.mwl-band-derived') : null;
    if (!cell) {
      return;
    }
    var hz = parseFloat(input.value);
    if (!isFinite(hz) || hz <= 0) {
      cell.textContent = '—';
      cell.removeAttribute('data-band');
      return;
    }
    cell.textContent = bandFor(hz) + ' · ' + wavelengthLabel(hz);
  }

  function init() {
    cuts = loadCuts();
    if (!cuts || !cuts.length) {
      return;
    }
    // Delegated, so rows added with "Add another" are covered too.
    document.addEventListener('input', function (event) {
      var target = event.target;
      if (target && target.classList && target.classList.contains('mwl-frequency')) {
        update(target);
      }
    });
    Array.prototype.forEach.call(
      document.querySelectorAll('.mwl-frequency'), update);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
