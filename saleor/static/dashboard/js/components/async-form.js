export default $(document).on('submit', '.form-async', function (e) {
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
}).on('click', '.modal-close', function () {
  $('.modal').modal('close');
});
