/* @flow */

import React from 'react';
import {render} from 'react-dom';
import {Provider} from 'react-redux';
import {createStore} from 'redux';
import $ from 'jquery';
import AddressForm  from './components/addressform';
import {CartItemAmount, CartItemSubtotal, CartTotal} from './components/cart';
import storeApp from './reducers';
require('jquery.cookie');
require('bootstrap-sass');

let store = createStore(storeApp, window.__INITIAL_STATE__);

var textInput = [];
var options = [1,2,3,4,5,6,7,8,9,10];
var csrftoken = $.cookie('csrftoken');
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

$(".cart-item-amount").each(function(index) {
  var $input = $(this).find("input");
  var $button = $(this).find("button");
  var value = $input.val();
  var name = $input.attr("name");
  var max = $input.attr("max");
  var props = {
    className: "",
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
  render(<Provider store={store}>
    <CartItemAmount {...props} />
  </Provider>, this);
});

let $cartTotal = $(".cart-total");
if ($cartTotal.length) {
  render(<Provider store={store}>
    <CartTotal />
  </Provider>, $cartTotal[0]);
}

$('.cart-item-subtotal').each(function() {
  let productId = $(this).data('product-id');
  render(<Provider store={store}>
    <CartItemSubtotal productId={productId} />
  </Provider>, this);
});

$(function () {
  let $address = $('.i18n-address');
  if ($address.length === 0) {
    return;
  }
  let addressUrl = $address.data('address-url');
  let prefixName = (name, prefix) => (prefix ? `${prefix}-${name}` : name);
  $.ajax({
    url: addressUrl,
    dataType: 'json',
    cache: false,
    success: (data) => {
      render(
        <Provider store={store}>
          <AddressForm data={data} />
        </Provider>,
        $address[0]
      );
    }
  });
});

$(function() {
    let $carousel = $('.carousel');
    let $items = $('.product-gallery-item');
    let $modal = $('.modal');

    $items.on('click', function(e) {
        if ($('.carousel').is(':visible')) {
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
