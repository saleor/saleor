import SVGInjector from 'svg-injector-2';

import {initSelects} from './utils';

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
});
