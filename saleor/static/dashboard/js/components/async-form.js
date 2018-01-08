import { initSelects } from './selects';

const onAsyncFormSubmit = (e) => {
  const $target = $(e.currentTarget);
  $.ajax({
    url: $target.attr('action'),
    method: 'POST',
    data: $target.serialize(),
    complete: (response) => {
      // Write HTML if got 400 response, otherwise pretend nothing happened
      if (response.status === 400) {
        $target.parent().html(response.responseText);
        initSelects();
      } else {
        $('.modal-close').click();
      }
    },
    success: (response) => {
      if (response.redirectUrl) {
        window.location.href = response.redirectUrl;
      } else {
        location.reload();
      }
    }
  });
  e.preventDefault();
};

const onModalClose = () => $('.modal').modal('close');

// -----

$(document)
  .on('submit', '.form-async', onAsyncFormSubmit)
  .on('click', '.modal-close', onModalClose);
