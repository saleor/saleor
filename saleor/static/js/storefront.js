import '../scss/storefront.scss';
import 'jquery.cookie';
import React from 'react';
import ReactDOM from 'react-dom';
import SVGInjector from 'svg-injector-2';

import variantPickerStore from './stores/variantPicker';

import passwordIvisible from '../images/pass_invisible.svg';
import passwordVisible from '../images/pass_visible.svg';

import VariantPicker from './components/variantPicker/VariantPicker';
import VariantPrice from './components/variantPicker/VariantPrice';
import ProductSchema from './components/variantPicker/ProductSchema';

import './mobile/navbar';
import './mobile/search';
import './mobile/filters-menu';
import './components/cart';
import './components/sorter';

let csrftoken = $.cookie('csrftoken');

function csrfSafeMethod(method) {
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader('X-CSRFToken', csrftoken);
    }
  }
});

new SVGInjector().inject(document.querySelectorAll('svg[data-src]'));

let getAjaxError = (response) => {
  let ajaxError = $.parseJSON(response.responseText).error.quantity;
  return ajaxError;
};

// Sticky footer

let navbarHeight = $('.navbar').outerHeight(true);
let footerHeight = $('.footer').outerHeight(true);
let windowHeight = $(window).height();
$('.maincontent').css('min-height', windowHeight - navbarHeight - footerHeight);

// New address dropdown

let $addressShow = $('.address_show label');
let $addressHide = $('.address_hide label');
let $addressForm = $('.checkout__new-address');
let $initialValue = $('#address_new_address').prop('checked');
$addressShow.click((e) => {
  $addressForm.slideDown('slow');
});
$addressHide.click((e) => {
  $addressForm.slideUp('slow');
});
if ($initialValue) {
  $addressForm.slideDown(0);
} else {
  $addressForm.slideUp(0);
}

// Smart address form

$(function () {
  const $i18nAddresses = $('.i18n-address');
  $i18nAddresses.each(function () {
    const $form = $(this).closest('form');
    const $countryField = $form.find('select[name=country]');
    const $previewField = $form.find('input.preview');
    $countryField.on('change', () => {
      $previewField.val('on');
      $form.submit();
    });
  });
});

// Input Passwords

let $inputPassword = $('input[type=password]');
$("<img class='passIcon' src=" + passwordIvisible + " />").insertAfter($inputPassword);
$inputPassword.parent().addClass('relative');
$('.passIcon').on('click', (e) => {
  let $input = $(e.target).parent().find('input');
  if ($input.attr('type') == 'password') {
    $input.attr('type', 'text');
    $(e.target).attr('src', passwordVisible);
  } else {
    $input.attr('type', 'password');
    $(e.target).attr('src', passwordIvisible);
  }
});

// Delivery information

let $deliveryForm = $('.deliveryform');
let crsfToken = $deliveryForm.data('crsf');
let countrySelect = '#id_country';
let $cartSubtotal = $('.cart__subtotal');
let deliveryAjax = (e) => {
  let newCountry = $(countrySelect).val();
  $.ajax({
    url: '/cart/shipingoptions/',
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

// Open tab from the link

let hash = window.location.hash;
$('.nav-tabs a[href="' + hash + '"]').tab('show');

// Variant Picker

const variantPickerContainer = document.getElementById('variant-picker');
const variantPriceContainer = document.getElementById('variant-price-component');

if (variantPickerContainer) {
  const variantPickerData = JSON.parse(variantPickerContainer.dataset.variantPickerData);
  ReactDOM.render(
    <VariantPicker
      onAddToCartError={onAddToCartError}
      onAddToCartSuccess={onAddToCartSuccess}
      store={variantPickerStore}
      url={variantPickerContainer.dataset.action}
      variantAttributes={variantPickerData.variantAttributes}
      variants={variantPickerData.variants}
    />,
    variantPickerContainer
  );

  if (variantPriceContainer) {
    ReactDOM.render(
      <VariantPrice
        availability={variantPickerData.availability}
        store={variantPickerStore}
      />,
      variantPriceContainer
    );
  }
}

// Product Schema
const productSchemaContainer = document.getElementById('product-schema-component');
if (productSchemaContainer) {
  let productSchema = JSON.parse(document.getElementById('product-schema-component').children[0].text);
  ReactDOM.render(
    <ProductSchema
      variantStore={variantPickerStore}
      productSchema={productSchema}
    />,
    productSchemaContainer
  );
}


// Account delete address bar

let $deleteAdressIcons = $('.icons');
let $deleteAdressIcon = $('.delete-icon');
let $deleteAddress = $('.address-delete');

$deleteAdressIcon.on('click', (e) => {
  if ($deleteAddress.hasClass('none')) {
    $deleteAddress.removeClass('none');
    $deleteAdressIcons.addClass('none');
  } else {
    $deleteAddress.addClass('none');
  }
});

$deleteAddress.find('.cancel').on('click', (e) => {
  $deleteAddress.addClass('none');
  $deleteAdressIcons.removeClass('none');
});


// Cart quantity form

let $cartLine = $('.cart__line');
let $total = $('.cart-subtotal');
let $cartBadge = $('.navbar__brand__cart .badge');
let $removeProductSucces = $('.remove-product-alert');
let $closeMsg = $('.close-msg');
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
        if (newQuantity == 0) {
          if (response.cart.numLines == 0) {
            $.cookie('alert', 'true', {path: '/cart'});
            location.reload();
          } else {
            $removeProductSucces.removeClass('hidden-xs-up');
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
          $removeProductSucces.removeClass('hidden-xs-up');
        } else {
          $.cookie('alert', 'true', {path: '/cart'});
          location.reload();
        }
        deliveryAjax();
      }
    });
  });
});

// StyleGuide fixed menu

$(document).ready(function () {
  let styleGuideMenu = $('.styleguide__nav');
  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      styleGuideMenu.addClass("fixed");
    } else {
      styleGuideMenu.removeClass("fixed");
    }
  });
});

if ($.cookie('alert') === 'true') {
  $removeProductSucces.removeClass('hidden-xs-up');
  $.cookie('alert', 'false', {path: '/cart'});
}

$closeMsg.on('click', (e) => {
  $removeProductSucces.addClass('hidden-xs-up');
});


$('.toggle-filter').each(function () {
  let icon = $(this).find('.collapse-filters-icon');
  let ele = $(this).find('.filter-form-field');

  let filterArrowDown = $('.product-filters__attributes').data('icon-down');
  let filterArrowUp = $('.product-filters__attributes').data('icon-up');

  ele.attr('aria-expanded', '');

  $(this).find('.filter-label').on('click', () => {
    if (ele.attr('aria-expanded') !== undefined) {
      ele.removeAttr('aria-expanded').find('input[type="checkbox"], input[type="number"]').each((i, el) => {
        if (!el.checked) {
          $(el.parentNode.parentNode).addClass('d-none');
        }
      });
      icon.find('img').attr('src', filterArrowDown);
    } else {
      ele.attr('aria-expanded', '').find('input[type="checkbox"], input[type="number"]').each((i, el) => {
        $(el.parentNode.parentNode).removeClass('d-none');
      });
      icon.find('img').attr('src', filterArrowUp);
    }
  });
});
