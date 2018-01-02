import SVGInjector from 'svg-injector-2';

import { initSelects, onScroll } from './utils';

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
$(document).on('click', 'tr[data-action-go]>td:not(.ignore-link)', (e) => {
  const $targetElement = $(e.currentTarget).parent();
  window.location.href = $targetElement.data('action-go');
});

// Publish / unpublish lever in product detail view
$('#product-is-published').on('click', (e) => {
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
    })
  }
});

// Styleguide sticky right menu
onScroll(() => $('.styleguide__menu').toggleClass('fixed', $(window).scrollTop() > 100));

export {
  screenSizes,
  svgInjector
};
