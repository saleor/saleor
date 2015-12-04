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
  let lang = $address.data('lang');
  let prefix = $address.data('prefix');
  let addressMapping = [
    {fieldName: 'country', messageType: 'SET_COUNTRY', messageField: 'country'},
    {fieldName: 'country_area', messageType: 'SET_LEVEL1', messageField: 'level1'},
    {fieldName: 'city', messageType: 'SET_LEVEL2', messageField: 'level2'},
    {fieldName: 'city_area', messageType: 'SET_LEVEL3', messageField: 'level3'},
    {fieldName: 'first_name', messageType: 'SET_FIRST_NAME', messageField: 'firstName'},
    {fieldName: 'last_name', messageType: 'SET_LAST_NAME', messageField: 'lastName'},
    {fieldName: 'company_name', messageType: 'SET_ORGANIZATION', messageField: 'organization'},
    {fieldName: 'postal_code', messageType: 'SET_POSTCODE', messageField: 'postcode'},
    {fieldName: 'street_address_1', messageType: 'SET_ADDRESS1', messageField: 'address1'},
    {fieldName: 'street_address_2', messageType: 'SET_ADDRESS2', messageField: 'address2'}
  ];
  let prefixName = (name, prefix) => (prefix ? `${prefix}-${name}` : name);
  addressMapping.map(({fieldName, messageType, messageField}) => {
    let name = prefixName(fieldName, prefix);
    let input = $address.find(`[name=${name}]`);
    let value = '';
    if (input.length !== 0) {
      value = input.val();
    }
    let message = {type: messageType, [messageField]: value};
    store.dispatch(message);
  });
  let $countryField = $address.find(`[name=${prefixName('country', prefix)}]`);
  let countries = $countryField.find('option').map((option, item) => ({code: item.value, label: item.label})).get();
  $.ajax({
    url: addressUrl,
    dataType: 'json',
    cache: false,
    success: (data) => {
      render(
        <Provider store={store}>
          <AddressForm lang={lang} countries={countries} data={data} prefix={prefix} />
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
