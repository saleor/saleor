/* @flow */

import React from 'react';
import {render} from 'react-dom';
import {Provider} from 'react-redux';
import $ from 'jquery';
import {CartItemAmount, CartItemSubtotal, CartTotal} from './components/cart';
import CartStore from './stores/cart-store';
require('jquery.cookie');
require('bootstrap-sass');

let textInput = [];
let options = [1,2,3,4,5,6,7,8,9,10];
let csrftoken = $.cookie('csrftoken');

function csrfSafeMethod(method) {
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader('X-CSRFToken', csrftoken);
    }
  }
});

$('.cart-item-amount').each(function(index) {
  let $input = $(this).find('input');
  let $button = $(this).find('button');
  let value = $input.val();
  let name = $input.attr('name');
  let max = $input.attr('max');
  let props = {
    className: '',
    index: index,
    max: max,
    options: options.slice(0, max),
    thresholdValue: options[options.length - 1],
    url: $(this).find('form').attr('action'),
    fieldName: name,
    value: value
  };
  $(this).find('.cart-item-quantity').removeClass('js-hidden');
  $button.addClass('invisible');
  textInput.push(this.firstElementChild);
  render(<Provider store={CartStore}>
    <CartItemAmount {...props} />
  </Provider>, this);
});

let $cartTotal = $('.cart-total');
let cartTotalValue = $cartTotal.text();
if ($cartTotal.length) {
  CartStore.dispatch({type: 'UPDATE_TOTAL', total: cartTotalValue});
  render(<Provider store={CartStore}>
    <CartTotal />
  </Provider>, $cartTotal[0]);
}

$('.cart-item-subtotal').each(function() {
  let productId = $(this).data('product-id');
  let props = {
    productId,
    subtotal: $(this).text()
  };
  CartStore.dispatch({type: 'UPDATE_SUBTOTAL', ...props});
  render(<Provider store={CartStore}>
    <CartItemSubtotal productId={productId} />
  </Provider>, this);
});

$(function() {
  let $carousel = $('.carousel');
  let $items = $('.product-gallery-item');
  let $modal = $('.modal');

  $items.on('click', function(e) {
    if ($carousel.is(':visible')) {
      e.preventDefault();
    }
    let index = $(this).index();
    $carousel.carousel(index);
  });

  $modal.on('show.bs.modal', function() {
    let $img = $(this).find('.modal-body img');
    let dataSrc = $img.attr('data-src');
    $img.attr('src', dataSrc);
  });
});

$(function() {
  $('.conditional-visibility').each(function() {
    let $element = $(this);
    let controller = $element.data('controller');
    let triggerValue = $element.data('value');
    let $controller = $(controller);
    function updateVisiblity() {
      let value = $controller.filter(':checked').val();
      if (!value && $controller.prop('type') === 'hidden') {
        value = $controller.val();
      }
      if (value === triggerValue) {
        $element.show();
      } else {
        $element.hide();
      }
    }
    $controller.on('change', updateVisiblity);
    updateVisiblity();
  });
});
