import 'select2';

let supportsPassive = false;
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
  $('select:not(.browser-default):not(.enable-ajax-select2):not([multiple])').material_select();
  $('select[multiple]:not(.browser-default):not(.enable-ajax-select2)').select2({width: '100%'});

  let $ajaxSelect2Elements = $('select.enable-ajax-select2');
  $ajaxSelect2Elements.each(function() {
    let $select = $(this);

    if ($select.attr('data-initial')) {
      function appendOption(select, option) {
        $select.append($('<option></option>').attr(
          'value', option.id).text(option.text));
      }

      let initial = $select.data('initial');
      if (initial instanceof Array) {
        let selected = []
        initial.forEach(function(item) {
          appendOption($select, item);
          selected.push(item.id);
        });
        $select.val(selected);
      }
      else {
        appendOption($select, initial);
        $select.val(initial.id);
      }
    };

    let url = $select.data('url');
    $select.select2({
      ajax: {
        url: url,
        delay: 250
      },
      width: '100%',
      minimumInputLength: 2
    });
  });
}
