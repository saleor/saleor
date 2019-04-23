import {getAjaxError} from './misc';

export const summaryLink = $('html').data('checkout-summary-url');
export const $checkoutDropdown = $('.checkout-preview-dropdown');
export const $checkoutIcon = $('.checkout__icon');
export const $addToCheckoutError = $('.product__info__form-error small');
export const $removeProductSuccess = $('.remove-product-alert');

export const onAddToCheckoutError = (response) => {
  $addToCheckoutError.html(getAjaxError(response));
};

export const onAddToCheckoutSuccess = () => {
  $.get(summaryLink, (data) => {
    $checkoutDropdown.html(data);
    $addToCheckoutError.html('');
    var newQunatity = $('.checkout-preview-dropdown__total').data('quantity');
    $('.badge').html(newQunatity).removeClass('empty');
    $checkoutDropdown.addClass('show');
    $checkoutIcon.addClass('hover');
    $checkoutDropdown.find('.checkout-preview-dropdown__list').scrollTop($checkoutDropdown.find('.checkout-preview-dropdown__list')[0].scrollHeight);
    setTimeout((e) => {
      $checkoutDropdown.removeClass('show');
      $checkoutIcon.removeClass('hover');
    }, 2500);
  });
};

export default $(document).ready((e) => {
  // Checkout dropdown
  $.get(summaryLink, (data) => {
    $checkoutDropdown.html(data);
  });
  $('.navbar__brand__checkout').hover((e) => {
    $checkoutDropdown.addClass('show');
    $checkoutIcon.addClass('hover');
  }, (e) => {
    $checkoutDropdown.removeClass('show');
    $checkoutIcon.removeClass('hover');
  });
  $('.product-form button').click((e) => {
    e.preventDefault();
    let quantity = $('#id_quantity').val();
    let variant = $('#id_variant').val();
    $.ajax({
      url: $('.product-form').attr('action'),
      type: 'POST',
      data: {
        variant: variant,
        quantity: quantity
      },
      success: () => {
        onAddToCheckoutSuccess();
      },
      error: (response) => {
        onAddToCheckoutError(response);
      }
    });
  });
  $('.checkout__clear').click((e) => {
    $.ajax({
      url: $('.checkout__clear').data('action'),
      method: 'POST',
      data: {},
      success: (response) => {
        $('.badge').html(response.numItems);
        $.cookie('alert', 'true', {path: '/checkout'});
        location.reload();
      }
    });
  });

  // Checkout quantity form

  let $checkoutLine = $('.checkout-preview__line');
  let $total = $('.checkout-preview-subtotal');
  let $checkoutBadge = $('.navbar__brand__checkout .badge');
  let $closeMsg = $('.close-msg');
  $closeMsg.on('click', (e) => {
    $removeProductSuccess.addClass('d-none');
  });
  $checkoutLine.each(function () {
    let $quantityInput = $(this).find('#id_quantity');
    let checkoutFormUrl = $(this).find('.form-checkout').attr('action');
    let $qunatityError = $(this).find('.checkout-preview__line__quantity-error');
    let $subtotal = $(this).find('.checkout-preview-item-price p');
    let $deleteIcon = $(this).find('.checkout-preview-item-delete');
    $(this).on('change', $quantityInput, (e) => {
      let newQuantity = $quantityInput.val();
      $.ajax({
        url: checkoutFormUrl,
        method: 'POST',
        data: {quantity: newQuantity},
        success: (response) => {
          if (newQuantity === 0) {
            if (response.checkout.numLines === 0) {
              $.cookie('alert', 'true', {path: '/checkout'});
              location.reload();
            } else {
              $removeProductSuccess.removeClass('d-none');
              $(this).fadeOut();
            }
          } else {
            $subtotal.html(response.subtotal);
          }
          $checkoutBadge.html(response.checkout.numItems);
          $qunatityError.html('');
          $checkoutDropdown.load(summaryLink);
          deliveryAjax();
        },
        error: (response) => {
          $qunatityError.html(getAjaxError(response));
        }
      });
    });
    $deleteIcon.on('click', (e) => {
      $.ajax({
        url: checkoutFormUrl,
        method: 'POST',
        data: {quantity: 0},
        success: (response) => {
          if (response.checkout.numLines >= 1) {
            $(this).fadeOut();
            $total.html(response.total);
            $checkoutBadge.html(response.checkout.numItems);
            $checkoutDropdown.load(summaryLink);
            $removeProductSuccess.removeClass('d-none');
          } else {
            $.cookie('alert', 'true', {path: '/checkout'});
            location.reload();
          }
          deliveryAjax();
        }
      });
    });
  });

  // Delivery information

  let $deliveryForm = $('.deliveryform');
  let crsfToken = $deliveryForm.data('crsf');
  let countrySelect = '#id_country';
  let $checkoutSubtotal = $('.checkout__subtotal');
  let deliveryAjax = (e) => {
    let newCountry = $(countrySelect).val();
    $.ajax({
      url: $('html').data('shipping-options-url'),
      type: 'POST',
      data: {
        'csrfmiddlewaretoken': crsfToken,
        'country': newCountry
      },
      success: (data) => {
        $checkoutSubtotal.html(data);
      }
    });
  };

  $checkoutSubtotal.on('change', countrySelect, deliveryAjax);

  if ($.cookie('alert') === 'true') {
    $removeProductSuccess.removeClass('d-none');
    $.cookie('alert', 'false', {path: '/checkout'});
  }
});
