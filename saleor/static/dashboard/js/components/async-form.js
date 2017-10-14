import {initSelects} from './utils';

export default $(document).on('submit', '.form-async', function (e) {
  let that = this;
  $.ajax({
    url: $(that).attr('action'),
    method: 'post',
    data: $(that).serialize(),
    complete: function (response) {
      if (response.status === 400) {
        $(that).parent().html(response.responseText);
        initSelects();
      } else {
        $('.modal-close').click();
      }
    },
    success: function (response) {
      if (response.redirectUrl) {
        window.location.href = response.redirectUrl;
      } else {
        location.reload();
      }
    }
  });
  e.preventDefault();
}).on('click', '.modal-close', function () {
  $('.modal').modal('close');
});
