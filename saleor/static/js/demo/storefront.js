import '../../scss/demo/storefront.scss'
import 'jquery.cookie'

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

//Cart dropdown

var summaryLink = "/cart/summary"
var $cartDropdown = $(".cart-dropdown")
$.get(summaryLink, (data) => {
    $cartDropdown.html(data)
})
$('.navbar__brand__cart').hover((e) => {
  $cartDropdown.addClass("show")
}, (e) => {
  $cartDropdown.removeClass("show")
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
    success: function() {
      $.get(summaryLink, (data) => {
          $cartDropdown.html(data)
          var newQunatity = $('.cart-dropdown__total').data('quantity')
          $('.badge').html(newQunatity).removeClass('hidden-xs-up')
          $cartDropdown.addClass("show")
          setTimeout((e) => {
            $cartDropdown.removeClass('show')
          }, 2500)
      })
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
    url: "/cart/shipingoptions/",
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
