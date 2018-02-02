import passwordIvisible from '../../images/pass-invisible.svg';
import passwordVisible from '../../images/pass-visible.svg';

export default $(document).ready((e) => {
  let $inputPassword = $('input[type=password]');
  $('<img class="passIcon" src=' + passwordIvisible + ' />').insertAfter($inputPassword);
  $inputPassword.parent().addClass('relative');
  $('.passIcon').on('click', (e) => {
    let $input = $(e.target).parent().find('input');
    if ($input.attr('type') === 'password') {
      $input.attr('type', 'text');
      $(e.target).attr('src', passwordVisible);
    } else {
      $input.attr('type', 'password');
      $(e.target).attr('src', passwordIvisible);
    }
  });
});
