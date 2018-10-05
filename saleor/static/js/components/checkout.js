import {getAjaxError} from './misc';
export const $useVoucherError = $('.product__info__form-error small');

export const onUseVoucherError = (response) => {
  $useVoucherError.html(getAjaxError(response));
};

export default $(document).ready((e) => {
  $('.discount-form .btn').click((e) => {
    e.preventDefault();
    let voucher = $('#id_voucher').val();
    $.ajax({
      url: $('.discount-form').attr('action'),
      type: 'POST',
      data: {
        'discount': voucher,
      },
      success: (data) => {
        console.log("THE SUCCESS DATA:" + data)
      },
      error: (response) => {
        onUseVoucherError(response);
      }
    });
  });
});
