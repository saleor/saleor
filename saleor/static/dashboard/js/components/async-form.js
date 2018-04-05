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
    success: function (data) {
      const $message = $(data).find('div');
      $message.find('a').remove();
      const $lastRow = $target.find('.row').last();
      $lastRow.html($message);
      $lastRow.css('text-align', 'center');
      $lastRow.find('svg').height('160px');
      $target.find('button').remove();
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
