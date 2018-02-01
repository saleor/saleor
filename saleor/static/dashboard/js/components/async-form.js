import { initSelects } from './selects';

export default $(document).on('submit', '.form-async', function (e) {
  $.ajax({
    url: $(e.currentTarget).attr('action'),
    method: 'post',
    data: $(e.currentTarget).serialize(),
    success: function (data) {
      const $message = $(data).find('div');
      $message.find('a').remove();
      $(e.currentTarget).find('.row').last().html($message);
      $(e.currentTarget).find('.row').last().css('text-align', 'center');
      $(e.currentTarget).find('svg').height('160px');
      $(e.currentTarget).find('button').remove();
    }
  });
  e.preventDefault();
}).on('click', '.modal-close', function () {
  $('.modal').modal('close');
});
