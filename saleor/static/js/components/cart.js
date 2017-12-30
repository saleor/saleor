import {getAjaxError} from './misc';

export const summaryLink = $('html').data('cart-summary-url');
export const $cartDropdown = $('.cart-dropdown');
export const $cartIcon = $('.cart__icon');
export const $addToCartError = $('.product__info__form-error small');
export const $removeProductSuccess = $('.remove-product-alert');

export const onAddToCartError = (response) => {
  $addToCartError.html(getAjaxError(response));
};

export const onAddToCartSuccess = () => {
  $.get(summaryLink, (data) => {
    $cartDropdown.html(data);
    $addToCartError.html('');
    var newQunatity = $('.cart-dropdown__total').data('quantity');
    $('.badge').html(newQunatity).removeClass('empty');
    $cartDropdown.addClass('show');
    $cartIcon.addClass('hover');
    $cartDropdown.find('.cart-dropdown__list').scrollTop($cartDropdown.find('.cart-dropdown__list')[0].scrollHeight);
    setTimeout((e) => {
      $cartDropdown.removeClass('show');
      $cartIcon.removeClass('hover');
    }, 2500);
  });
};

export default $(document).ready((e) => {
  // Cart dropdown
  $.get(summaryLink, (data) => {
    $cartDropdown.html(data);
  });
  $('.navbar__brand__cart').hover((e) => {
    $cartDropdown.addClass('show');
    $cartIcon.addClass('hover');
  }, (e) => {
    $cartDropdown.removeClass('show');
    $cartIcon.removeClass('hover');
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
        onAddToCartSuccess();
      },
      error: (response) => {
        onAddToCartError(response);
      }
    });
  });

  // Cart quantity form

  let $cartLine = $('.cart__line');
  let $total = $('.cart-subtotal');
  let $cartBadge = $('.navbar__brand__cart .badge');
  let $closeMsg = $('.close-msg');
  $closeMsg.on('click', (e) => {
    $removeProductSuccess.addClass('d-none');
  });
  $cartLine.each(function () {
    let $quantityInput = $(this).find('#id_quantity');
    let cartFormUrl = $(this).find('.form-cart').attr('action');
    let $qunatityError = $(this).find('.cart__line__quantity-error');
    let $subtotal = $(this).find('.cart-item-price p');
    let $deleteIcon = $(this).find('.cart-item-delete');
    $(this).on('change', $quantityInput, (e) => {
      let newQuantity = $quantityInput.val();
      $.ajax({
        url: cartFormUrl,
        method: 'POST',
        data: {quantity: newQuantity},
        success: (response) => {
          if (newQuantity === 0) {
            if (response.cart.numLines === 0) {
              $.cookie('alert', 'true', {path: '/cart'});
              location.reload();
            } else {
              $removeProductSuccess.removeClass('d-none');
              $(this).fadeOut();
            }
          } else {
            $subtotal.html(response.subtotal);
          }
          $cartBadge.html(response.cart.numItems);
          $qunatityError.html('');
          $cartDropdown.load(summaryLink);
          deliveryAjax();
        },
        error: (response) => {
          $qunatityError.html(getAjaxError(response));
        }
      });
    });
    $deleteIcon.on('click', (e) => {
      $.ajax({
        url: cartFormUrl,
        method: 'POST',
        data: {quantity: 0},
        success: (response) => {
          if (response.cart.numLines >= 1) {
            $(this).fadeOut();
            $total.html(response.total);
            $cartBadge.html(response.cart.numItems);
            $cartDropdown.load(summaryLink);
            $removeProductSuccess.removeClass('d-none');
          } else {
            $.cookie('alert', 'true', {path: '/cart'});
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
  let $cartSubtotal = $('.cart__subtotal');
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
        $cartSubtotal.html(data);
      }
    });
  };

  $cartSubtotal.on('change', countrySelect, deliveryAjax);

  if ($.cookie('alert') === 'true') {
    $removeProductSuccess.removeClass('d-none');
    $.cookie('alert', 'false', {path: '/cart'});
  }
});
