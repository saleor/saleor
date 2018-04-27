import SVGInjector from 'svg-injector-2';

import { initSelects } from './selects';
import { onScroll } from './utils';

const screenSizes = {
  sm: 600,
  md: 992,
  lg: 1200
};

const svgInjector = new SVGInjector();

// -----

// Inject all SVGs
svgInjector.inject(document.querySelectorAll('svg[data-src]'));

// Custom select inputs
initSelects();

// Materialize modals
$('.modal').modal();

// Print button
$('.btn-print').click((e) => {
  window.print();
});

// Clickable rows in dashboard tables
$(document).on('mouseup', 'tr[data-action-go] > td:not(.ignore-link)', (e) => {
  const $target = $(e.currentTarget);
  // Ignore selecting text
  const selectedText = getSelection().toString();
  if (selectedText === '' || selectedText === $target.data('ignore-text')) {
    window.location.href = $target.parent().data('action-go');
  } else {
    $target.data('ignore-text', selectedText);
  }
});

// Publish / unpublish lever in detail views
const selectors = ['#product-is-published', '#collection-is-published'];
selectors.forEach(selector => {
  $(selector).on('click', (e) => {
    const form = $(e.currentTarget).closest('#toggle-publish-form');
    const input = form.find('#toggle-publish-switch')[0];
    if (e.target === input) {
      const url = form.attr('action');
      fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        }
      }).then(() => {
        window.location.reload();
      }).catch(() => {
        window.location.reload();
      });
    }
  });
});

// Styleguide sticky right menu
onScroll(() => $('.styleguide__menu').toggleClass('fixed', $(window).scrollTop() > 100));

export {
  screenSizes,
  svgInjector
};
