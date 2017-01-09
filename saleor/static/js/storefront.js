import '../scss/storefront/storefront.scss'
import 'jquery.cookie'
import React from 'react'
import ReactDOM from 'react-dom'

import VariantPicker from './components/variantPicker/VariantPicker'

let csrftoken = $.cookie('csrftoken')

function csrfSafeMethod(method) {
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method)
}

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader('X-CSRFToken', csrftoken)
    }
  }
})

var getAjaxError = (response) => {
  var ajaxError = $.parseJSON(response.responseText).error.quantity
  return ajaxError
}

// Mobile menu

$(document).ready((e) => {
  var $toogleIcon = $('.navbar__brand__menu-toggle')
  var $mobileNav = $('nav')
  var windowWidth = $(window).width()

  if (windowWidth < 767) {
    $mobileNav.append('<ul class="nav navbar-nav navbar__menu__login"></ul>')
    $('.navbar__login a').appendTo('.navbar__menu__login')
                         .wrap( '<li class="nav-item login-item"></li>')
                         .addClass('nav-link')
  }

  $toogleIcon.click((e) => {
    $mobileNav.toggleClass('open')
    event.stopPropagation()
  })
  $(document).click((e) => {
    $mobileNav.removeClass('open')
  })
})

// Mobile search form

var $searchIcon = $('.mobile-search-icon')
var $closeSearchIcon = $('.mobile-close-search')
var $searchForm = $('.navbar__brand__search')
$searchIcon.click((e) => {
  $searchForm.animate({left: 0}, {duration: 500})
})
$closeSearchIcon.click((e) => {
  $searchForm.animate({left: '-100vw'}, {duration: 500})
})

// Sticky footer

var navbarHeight = $('.navbar').outerHeight(true)
var footerHeight = $('.footer').outerHeight(true)
var windowHeight = $(window).height()
$('.maincontent').css('min-height', windowHeight - navbarHeight - footerHeight)

// New address dropdown

var $addressShow = $('.address_show label')
var $addressHide = $('.address_hide label')
var $addressForm = $('.checkout__new-address')
var $initialValue = $('#address_new_address').prop('checked')
$addressShow.click((e) => {
  $addressForm.slideDown('slow')
})
$addressHide.click((e) => {
  $addressForm.slideUp('slow')
})
if ($initialValue) {
  $addressForm.slideDown(0)
} else {
  $addressForm.slideUp(0)
}

// Smart address form

$(function() {
  const $i18nAddresses = $('.i18n-address')
  $i18nAddresses.each(function () {
    const $form = $(this).closest('form')
    const $countryField = $form.find('select[name=country]')
    const $previewField = $form.find('input.preview')
    $countryField.on('change', () => {
      $previewField.val('on')
      $form.submit()
    })
  })
})


//Cart dropdown

var summaryLink = '/cart/summary'
var $cartDropdown = $('.cart-dropdown')
var $addToCartError = $('.product__info__form-error')

const onAddToCartSuccess = () => {
  $.get(summaryLink, (data) => {
    $cartDropdown.html(data)
    $addToCartError.html('')
    var newQunatity = $('.cart-dropdown__total').data('quantity')
    $('.badge').html(newQunatity).removeClass('hidden-xs-up')
    $cartDropdown.addClass('show')
    $cartDropdown.find('.container').scrollTop($cartDropdown.find('.container')[0].scrollHeight)
    setTimeout((e) => {
      $cartDropdown.removeClass('show')
    }, 2500)
  })
}

const onAddToCartError = (response) => {
  $addToCartError.html(getAjaxError(response))
}

$.get(summaryLink, (data) => {
    $cartDropdown.html(data)
})
$('.navbar__brand__cart').hover((e) => {
  $cartDropdown.addClass('show')
}, (e) => {
  $cartDropdown.removeClass('show')
})
$('.product-form button').click((e) => {
  e.preventDefault()
  var quantity = $('#id_quantity').val()
  var variant = $('#id_variant').val()
  $.ajax ({
    url: $('.product-form').attr('action'),
    type: 'POST',
    data: {
      variant: variant,
      quantity: quantity
    },
    success: () => {
      onAddToCartSuccess()
    },
    error: (response) => {
      onAddToCartError(response)
    }
  })
})

// Delivery information

var $deliveryForm = $('.deliveryform')
var crsfToken = $deliveryForm.data('crsf')
var $countrySelect = $('#id_country')
var $newMethod = $('.cart__delivery-info__method')
var $newPrice = $('.cart__delivery-info__price')
$countrySelect.on('change', (e) => {
  var newCountry = $countrySelect.val()
  $.ajax({
    url: '/cart/shipingoptions/',
    type: 'POST',
    data: {
      'csrfmiddlewaretoken': crsfToken,
      'country': newCountry
    },
    success: (data) => {
      $newMethod.empty()
      $newPrice.empty()
      $.each(data.options, (key, val) => {
          $newMethod.append('<p>' + val.shipping_method__name + '</p>')
          $newPrice.append('<p>$' + val.price[1] + '</p>')
      })
    }
  })
})

// Save tab links to URL
  		  
$('.nav-tabs a').click((e) => {
  e.preventDefault()
  $(this).tab('show')
});
$('ul.nav-tabs li a:not(:first)').on('shown.bs.tab', (e) => {
  var id = $(e.target).attr('href').substr(1)
  window.location.hash = id
});
var hash = window.location.hash;
$('.nav-tabs a[href="' + hash + '"]').tab('show')

// Variant Picker

const variantPicker = document.getElementById('variant-picker')
if (variantPicker) {
  const variantPickerData = JSON.parse(variantPicker.dataset.variantPickerData)
  ReactDOM.render(
    <VariantPicker
      availability={variantPickerData.availability}
      onAddToCartError={onAddToCartError}
      onAddToCartSuccess={onAddToCartSuccess}
      productAttributes={variantPickerData.productAttributes}
      url={variantPicker.dataset.action}
      variantAttributes={variantPickerData.variantAttributes}
      variants={variantPickerData.variants}
    />,
    variantPicker
  )
}

// Cart quantity form

var $cartLine = $('.cart__line')
var $total = $('.cart-total')
var $cartBadge = $('.navbar__brand__cart .badge')
var $removeProductSucces = $('.remove-product-alert')
var $closeMsg = $('.close-msg')
$cartLine.each(function() {
  var $quantityInput = $(this).find('#id_quantity')
  var cartFormUrl = $(this).find('.form-cart').attr('action')
  var $qunatityError = $(this).find('.cart__line__quantity-error')
  var $subtotal = $(this).find('.cart-item-subtotal h3')
  var $deleteIcon = $(this).find('.cart-item-delete')
  $(this).on('change', $quantityInput, (e) => {
    var newQuantity = $quantityInput.val()
    $.ajax({
      url: cartFormUrl,
      method: 'POST',
      data: {quantity: newQuantity},
      success: (response) => {
        if (newQuantity == 0) {
          if (response.cart_length == 0) {
            $.cookie('alert', 'true', { path: '/cart' })
            location.reload()
          } else {
            $removeProductSucces.removeClass('hidden-xs-up')
            $(this).fadeOut()
          }
        } else {
          $subtotal.html(response.subtotal)
        }
        $total.html(response.total)
        $cartBadge.html(response.cart)
        $qunatityError.html('')
        $cartDropdown.load(summaryLink)
      },
      error: (response) => {
        $qunatityError.html(getAjaxError(response))
      }
    })
  })
  $deleteIcon.on('click', (e) => {
    $.ajax({
      url: cartFormUrl,
      method: 'POST',
      data: {quantity: 0},
      success: (response) => {
        if (response.cart_length >= 1) {
          $(this).fadeOut()
          $total.html(response.total)
          $cartBadge.html(response.cart)
          $cartDropdown.load(summaryLink)
          $removeProductSucces.removeClass('hidden-xs-up')
        } else {
          $.cookie('alert', 'true', { path: '/cart' })
          location.reload()
        }
      }
    })
  })
})

if ($.cookie('alert') == 'true') {
  $removeProductSucces.removeClass('hidden-xs-up')
  $.cookie('alert', 'false', { path: '/cart' })
}

$closeMsg.on('click', (e) => {
  $removeProductSucces.addClass('hidden-xs-up')
})
