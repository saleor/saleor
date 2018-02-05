const onAsyncFormSubmit = (e) => {
  const $target = $(e.currentTarget);
  $.ajax({
    url: $target.attr('action'),
    method: 'post',
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

const onModalClose = () => $('.modal').modal('close');

// -----

$(document)
  .on('submit', '.form-async', onAsyncFormSubmit)
  .on('click', '.modal-close', onModalClose);
