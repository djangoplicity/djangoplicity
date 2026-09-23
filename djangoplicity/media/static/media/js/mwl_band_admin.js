// Multiwavelength image admin: preview of the derived band.
//
// The editor types a wavelength in nanometres and the band of the spectrum
// follows from it, but the band is a property of the model, so it is only
// known once the row has been saved. This fills the read-only Band column in
// as the editor types, using the bounds the change form renders into
// #mwl-band-ranges from WAVELENGTH_BAND_RANGES.
(function () {
  'use strict';

  var SPEED_OF_LIGHT_NM = 2.99792458e17;   // nm/s
  var ranges = null;   // [[loNm, hiNm, label], ...] shortest wavelength first

  // Mirrors SUPERSCRIPT_DIGITS in djangoplicity/media/consts.py.
  var SUPERSCRIPT_DIGITS = {
    '-': '⁻', '0': '⁰', '1': '¹', '2': '²',
    '3': '³', '4': '⁴', '5': '⁵', '6': '⁶',
    '7': '⁷', '8': '⁸', '9': '⁹'
  };

  function loadRanges() {
    var node = document.getElementById('mwl-band-ranges');
    if (!node) {
      return null;
    }
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      return null;
    }
  }

  // Mirrors band_for_wavelength() on the model: the bands touch, so a value
  // on a bound goes to the higher energy band, and anything past the radio
  // end is pinned to radio.
  function bandFor(nm) {
    for (var i = 0; i < ranges.length; i++) {
      if (nm <= ranges[i][1]) {
        return ranges[i][2];
      }
    }
    return ranges[ranges.length - 1][2];
  }

  function superscript(number) {
    return String(number).replace(/[-0-9]/g, function (c) {
      return SUPERSCRIPT_DIGITS[c];
    });
  }

  // The frequency the wavelength comes to, as "3×10¹⁶ Hz" or "10⁸ Hz".
  // Mirrors frequency_label() on the model, carry rule included.
  function frequencyLabel(nm) {
    var hz = SPEED_OF_LIGHT_NM / nm;
    var exponent = Math.floor(Math.log(hz) / Math.LN10);
    var coefficient = Math.round((hz / Math.pow(10, exponent)) * 10) / 10;
    if (coefficient >= 10) {
      coefficient /= 10;
      exponent += 1;
    }
    if (coefficient === 1) {
      return '10' + superscript(exponent) + ' Hz';
    }
    return coefficient + '×' + '10' + superscript(exponent) + ' Hz';
  }

  function update(input) {
    var row = input.closest ? input.closest('tr') : null;
    var cell = row ? row.querySelector('.mwl-band-derived') : null;
    if (!cell) {
      return;
    }
    var nm = parseFloat(input.value);
    if (!isFinite(nm) || nm <= 0) {
      cell.textContent = '—';
      cell.removeAttribute('data-band');
      return;
    }
    cell.textContent = bandFor(nm) + ' · ' + frequencyLabel(nm);
  }

  function init() {
    ranges = loadRanges();
    if (!ranges || !ranges.length) {
      return;
    }
    // Delegated, so rows added with "Add another" are covered too.
    document.addEventListener('input', function (event) {
      var target = event.target;
      if (target && target.classList && target.classList.contains('mwl-wavelength')) {
        update(target);
      }
    });
    Array.prototype.forEach.call(
      document.querySelectorAll('.mwl-wavelength'), update);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
