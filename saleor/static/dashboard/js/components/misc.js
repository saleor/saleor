import SVGInjector from 'svg-injector-2';

import { initSelects } from './utils';

export default $(document).ready((e) => {
  new SVGInjector().inject(document.querySelectorAll('svg[data-src]'));

  initSelects();
  $('.modal').modal();

  // Print button
  $('.btn-print').click((e) => {
    window.print();
  });

  // Clickable rows in dashboard tables
  $(document).on('click', 'tr[data-action-go]>td:not(.ignore-link)', function () {
    let target = $(this).parent();
    window.location.href = target.data('action-go');
  });

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
      }).then((r) => {
        return r.json();
      }).then((r) => {
        window.location.reload();
      });
    }
    return 1;
  });
});

export const screenSizes = {
  sm: 600,
  md: 992,
  lg: 1200
};
