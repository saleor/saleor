import 'select2';

var supportsPassive = false;
try {
  let opts = Object.defineProperty({}, 'passive', {
    get: function () {
      supportsPassive = true;
    }
  });
  window.addEventListener('test', null, opts);
} catch (e) {
}

export function onScroll(func) {
  window.addEventListener('scroll', func, supportsPassive ? {passive: true} : false);
}

export function initSelects() {
  $('select:not(.browser-default):not([multiple])').material_select();
  $('select[multiple]:not(.browser-default)').select2({width: '100%'});
}
