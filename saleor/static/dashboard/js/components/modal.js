import {initSelects} from './utils';
import SVGInjector from 'svg-injector-2';

export default $(document).ready((e) => {
  $('body').on('click', '.modal-trigger-custom', function (e) {
    let that = this;
    $.ajax({
      url: $(this).data('href'),
      method: 'get',
      success: function (response) {
        let $modal = $($(that).attr('href'));
        $modal.html(response);
        initSelects();
        $modal.modal('open');
        // Image checkbox selector
        $('.image_select-item-overlay').on('click', function (e) {
          let id = $(e.target).attr('id');
          let checkbox = $('input#' + id).prop('checked');
          $('input#' + id).prop('checked', !checkbox);
          $(e.target).toggleClass('checked', !checkbox);
        });
        new SVGInjector().inject(document.querySelectorAll('.modal-content svg[data-src]:not(.injected-svg)'));
      }
    });

    e.preventDefault();
  });
});
