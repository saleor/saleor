export default $(document).ready((e) => {
  let summaryLink = '/cart/summary/';
  let $cartDropdown = $('.cart-dropdown');
  let $cartIcon = $('.cart__icon');
  let $addToCartError = $('.product__info__form-error small');

  const onAddToCartSuccess = () => {
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

  const onAddToCartError = (response) => {
    $addToCartError.html(getAjaxError(response));
  };

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
});
