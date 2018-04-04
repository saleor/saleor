import { initSelects } from './selects';

const onAsyncFormSubmit = (e) => {
  const $target = $(e.currentTarget);
  let $action = $target.attr('action');
  const $submitButton = $target.find('button[type=submit][clicked=true]');
  const $formAction = $submitButton.attr('formaction');
  if (typeof $formAction !== typeof undefined && $formAction !== false) {
    $action = $formAction;
  }
  $.ajax({
    url: $action,
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

const onAsyncFormButtonClick = (e) => {
  const $button = $(e.currentTarget);
  const $formAsync = $button.parents('.form-async');
  $('button[type=submit]', $formAsync).removeAttr('clicked');
  $button.attr('clicked', 'true');
};

const onModalClose = () => $('.modal').modal('close');

// -----

$(document)
  .on('click', '.form-async button[type=submit]', onAsyncFormButtonClick)
  .on('submit', '.form-async', onAsyncFormSubmit)
  .on('click', '.modal-close', onModalClose);
