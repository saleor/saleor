import '../scss/storefront/storefront.scss';
import 'jquery.cookie';
import React from 'react';
import ReactDOM from 'react-dom';
import Relay from 'react-relay';

import variantPickerStore from './stores/variantPicker';

import passwordIvisible from '../images/pass-invisible.svg';
import passwordVisible from '../images/pass-visible.svg';

import VariantPicker from './components/variantPicker/VariantPicker';
import VariantPrice from './components/variantPicker/VariantPrice';
import ProductSchema from './components/variantPicker/ProductSchema';
import WishlistButton from './components/wishlistButton';

let csrftoken = $.cookie('csrftoken');

function csrfSafeMethod (method) {
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader('X-CSRFToken', csrftoken);
    }
  }
});

Relay.injectNetworkLayer(
  new Relay.DefaultNetworkLayer('/graphql/', {
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': csrftoken
    }
  })
);

let getAjaxError = (response) => {
  let ajaxError = $.parseJSON(response.responseText).error.quantity;
  return ajaxError;
};

// Mobile menu

$(document).ready((e) => {
  let $toogleIcon = $('.navbar__brand__menu-toggle');
  let $mobileNav = $('nav');
  let windowWidth = $(window).width();

  if (windowWidth < 767) {
    $mobileNav.append('<ul class="nav navbar-nav navbar__menu__login"></ul>');
    $('.navbar__login a').appendTo('.navbar__menu__login')
                         .wrap('<li class="nav-item login-item"></li>')
                         .addClass('nav-link');
  }

  $toogleIcon.click((e) => {
    $mobileNav.toggleClass('open');
    event.stopPropagation();
  });
  $(document).click((e) => {
    $mobileNav.removeClass('open');
  });
});

// Mobile search form

let $searchIcon = $('.mobile-search-icon');
let $closeSearchIcon = $('.mobile-close-search');
let $searchForm = $('.navbar__brand__search');
$searchIcon.click((e) => {
  $searchForm.animate({left: 0}, {duration: 500});
});
$closeSearchIcon.click((e) => {
  $searchForm.animate({left: '-100vw'}, {duration: 500});
});

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

$(function() {
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
$("<img class='passIcon' src="+passwordIvisible+" />").insertAfter($inputPassword);
$inputPassword.parent().addClass('relative');
$('.passIcon').on('click', (e) => {
  let $input = $(e.target).parent().find('input');
  if ($input.attr('type') == 'password') {
    $input.attr('type','text');
    $(e.target).attr('src', passwordVisible);
  } else {
    $input.attr('type','password');
    $(e.target).attr('src', passwordIvisible);
  }
});

// Cart dropdown

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

// Delivery information

let $deliveryForm = $('.deliveryform');
let crsfToken = $deliveryForm.data('crsf');
let $countrySelect = $('#id_country');
let $newMethod = $('.cart__delivery-info__method');
let $newPrice = $('.cart__delivery-info__price');
$countrySelect.on('change', (e) => {
  let newCountry = $countrySelect.val();
  $.ajax({
    url: '/cart/shipingoptions/',
    type: 'POST',
    data: {
      'csrfmiddlewaretoken': crsfToken,
      'country': newCountry
    },
    success: (data) => {
      $newMethod.empty();
      $newPrice.empty();
      $.each(data.options, (key, val) => {
        $newMethod.append('<p>' + val.shipping_method__name + '</p>');
        $newPrice.append('<p>$' + val.price[1] + '</p>');
      });
    }
  });
});

// Save tab links to URL

$('.nav-tabs a').click((e) => {
  e.preventDefault();
  $(this).tab('show');
});
$('ul.nav-tabs li a:not(:first)').on('shown.bs.tab', (e) => {
  let id = $(e.target).attr('href').substr(1);
  window.location.hash = id;
});
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
  let productSchema = JSON.parse(document.getElementById('product-schema-component').children[0].text)
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

// Wishlist button

const addToWishlistContainer = document.getElementById('add-to-wishlist');
const variantSelector = document.getElementById('id_variant');

if (addToWishlistContainer) {
  ReactDOM.render(
    <WishlistButton
      product={addToWishlistContainer.dataset.product}
      variantStore={variantPickerStore}
      wishlistUrl={addToWishlistContainer.dataset.wishlisturl}
      variantSelector={variantSelector}
    />,
    addToWishlistContainer
  );
}

// Cart quantity form

let $cartLine = $('.cart__line');
let $total = $('.cart-total');
let $cartBadge = $('.navbar__brand__cart .badge');
let $removeProductSucces = $('.remove-product-alert');
let $closeMsg = $('.close-msg');
$cartLine.each(function() {
  let $quantityInput = $(this).find('#id_quantity');
  let cartFormUrl = $(this).find('.form-cart').attr('action');
  let $qunatityError = $(this).find('.cart__line__quantity-error');
  let $subtotal = $(this).find('.cart-item-subtotal p');
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
            $.cookie('alert', 'true', { path: '/cart' });
            location.reload();
          } else {
            $removeProductSucces.removeClass('hidden-xs-up');
            $(this).fadeOut();
          }
        } else {
          $subtotal.html(response.subtotal);
        }
        $total.html(response.total);
        $cartBadge.html(response.cart.numItems);
        $qunatityError.html('');
        $cartDropdown.load(summaryLink);
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
          $.cookie('alert', 'true', { path: '/cart' });
          location.reload();
        }
      }
    });
  });
});

if ($.cookie('alert') === 'true') {
  $removeProductSucces.removeClass('hidden-xs-up');
  $.cookie('alert', 'false', { path: '/cart' });
}

$closeMsg.on('click', (e) => {
  $removeProductSucces.addClass('hidden-xs-up');
});

// Delete modal

$('.modal-trigger-custom').on('click', function (e) {
  let that = this;
  $.ajax({
    url: $(this).data('href'),
    method: 'get',
    success: function (response) {
      var $modal = $($(that).attr('href'));
      $modal.html(response);
      $modal.modal();
    }
  });

  e.preventDefault();
});
