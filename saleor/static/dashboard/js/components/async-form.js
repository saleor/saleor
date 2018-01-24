import { initSelects } from './selects';

export default $(document).on('submit', '.form-async', function (e) {
  let that = this;
  $.ajax({
    url: $(that).attr('action'),
    method: 'post',
    data: $(that).serialize(),
    success: function (data) {
      let $message = $(data).find('div');
      $message.find('a').remove();
      $(that).find('.row').last().html($message);
      $(that).find('.row').last().css('text-align', 'center');
      $(that).find('svg').height('160px');
      $(that).find('button').remove();
    }
  });
  e.preventDefault();
}).on('click', '.modal-close', function () {
  $('.modal').modal('close');
});
