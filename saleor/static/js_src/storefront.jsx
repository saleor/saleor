/* @flow */

import React from 'react';
import {render} from 'react-dom';
import {Provider} from 'react-redux';
import $ from 'jquery';
import {AddressForm} from './components/addressform';
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

$(function () {
  let $address = $('.i18n-address');
  let addressUrl = $address.data('address-url');
  $.ajax({
    url: addressUrl,
    dataType: 'json',
    cache: false,
    success: function (data) {
      let countries = [
        'AC', 'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ',
        'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ',
        'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CV', 'CW', 'CX', 'CY', 'CZ',
        'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ',
        'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET',
        'FI', 'FJ', 'FK', 'FM', 'FO', 'FR',
        'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY',
        'HK', 'HM', 'HN', 'HR', 'HT', 'HU',
        'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS',
        'IT', 'JE', 'JM', 'JO', 'JP', 'KE',
        'KG', 'KH', 'KI', 'KM', 'KN', 'KR', 'KW', 'KY', 'KZ',
        'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY',
        'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ',
        'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ',
        'OM',
        'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY',
        'QA',
        'RE', 'RO', 'RS', 'RU', 'RW', 'SA',
        'SB', 'SC', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SZ',
        'TA', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ',
        'UA', 'UG', 'UM', 'US', 'UY', 'UZ',
        'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU',
        'WF', 'WS',
        'XK',
        'YE', 'YT',
        'ZA', 'ZM', 'ZW'
      ];
      render(<AddressForm lang="it" countries={countries} country="CN" data={data} />, $address[0]);
    }.bind(this),
    error: function (xhr, status, err) {
      console.error(status, err.toString());
    }.bind(this)
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
