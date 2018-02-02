import { svgInjector } from './misc';
import { initSelects } from './selects';

// List of input types that can be autofocused after opening modal
const focusInputs = [
  'textarea',
  'input[type="text"]:not(.select-dropdown)',
  'input[type="number"]'
];

// -----

$('body').on('click', '.modal-trigger-custom', (e) => {
  const target = e.currentTarget;
  e.preventDefault();
  $.ajax({
    url: target.dataset.href,
    method: 'GET',
    success: (response) => {
      const $modal = $(target.getAttribute('href'));
      $modal
        .html(response)
        .modal('open');
      initSelects();
      const inputs = $modal.find(focusInputs.join(','));

      // Automatically focus first autofocusable input in modal after opening
      if (inputs.length) {
        $modal.find(focusInputs.join(','))[0].focus();
      }

      // Image checkbox selector
      $('.image_select-item-overlay').on('click', (e) => {
        const imageId = e.currentTarget.getAttribute('id');
        const checkbox = document.querySelector('input#' + imageId);
        const checkboxState = checkbox.getAttribute('checked');
        checkbox.setAttribute('checked', !checkboxState);
        $(e.target).toggleClass('checked', !checkbox);
      });

      // Inject all SVGs from modal
      svgInjector.inject(document.querySelectorAll('.modal-content svg[data-src]:not(.injected-svg)'));
    }
  });
});
