import Dropzone from 'dropzone'
import $ from 'jquery'
import 'materialize-css/dist/js/materialize'
import 'select2'
import Sortable from 'sortablejs'

import '../scss/dashboard.scss'

function openModal() {
  $('.modal-trigger-custom').on('click', function (e) {
    var that = this
    $.ajax({
      url: $(this).data('href'),
      method: 'get',
      success: function (response) {
        var $modal = $($(that).attr('href'))
        $modal.html(response)
        initSelects()
        $modal.openModal()
      }
    })

    e.preventDefault()
  })
}

$(document).ready(function() {
  var tabletScreen = 990
  var wideScreen = 1650
  var navWidth = '250px'
  var $mainNav = $('#main-nav')
  var mainNavTop = $mainNav.offset().top
  var $menuToggle = $('.menu-toggle')
  var $closeMenu = $('#close-menu')
  var $openMenu = $('#open-menu')
  function openMenu(animationSpeed) {
    $mainNav.animate({
      'left': navWidth
    }, animationSpeed)
    if ($(window).width() < wideScreen && $(window).width() >= tabletScreen) {
      $('main .container, .subheader .nav-wrapper').animate({
        'marginLeft': navWidth
      }, animationSpeed)
    }
    $openMenu.addClass('hide')
    $closeMenu.removeClass('hide')
    $(window).scroll(function() {
      $mainNav.toggleClass('sticky', $(window).scrollTop() > mainNavTop)
    })
    if ($(window).width() > tabletScreen) {
      $.cookie('menu', 'open', { path: '/' })
    }
  }
  function closeMenu() {
    $mainNav.animate({
      'left': '0'
    })
    $closeMenu.addClass('hide')
    $openMenu.removeClass('hide')
    $.removeCookie('menu', { path: '/' })
    if ($(window).width() < wideScreen) {
      $('main .container, .subheader .nav-wrapper').css({
        'margin-left': 'auto'
      })
    }
  }
  $openMenu.click(function() {
    openMenu(400)
  })
  $closeMenu.click(function() {
    closeMenu()
  })
  if ($(window).width() <= tabletScreen) {
    $(window).click(function() {
      closeMenu()
    });
    $openMenu.click(function(event) {
        event.stopPropagation();
    });
  }
  if ($.cookie('menu') == 'open') {
    openMenu(0)
  } else {
    closeMenu()
  }
  initSelects()
  $('.modal-trigger').leanModal()

  if (isTablet()) {
    $('.equal-height-on-med').matchHeight()
  }

  var $tabs = $('ul.tabs')
  if ($tabs.length) {
    $tabs.find('.tab').on('click', function (e) {
      window.history.pushState(null, null, e.target.hash)
      var tabSelector = $(this).find('a').attr('href')
      $('.btn-fab').addClass('btn-fab-hidden')
      $(tabSelector + '-btn').removeClass('btn-fab-hidden')
    })

    $tabs.find('a.active').parent().click()
  }
  openModal()
  var $messages = $('.message')
  var timeout = 0
  var offset = 100
  var firstMessageOffset = 250
  setTimeout(function() {
    $messages.each(function () {
      var that = this
      setTimeout(function () {
        $(that).removeClass('toast--hidden')
      }, timeout + offset)
      timeout += 3000
      setTimeout(function () {
        $(that).addClass('toast--hidden')
      }, timeout - offset)
    })
  }, firstMessageOffset)

  $(document).on('submit', '.form-async', function(e) {
    var that = this
    $.ajax({
      url: $(that).attr('action'),
      method: 'post',
      data: $(that).serialize(),
      complete: function(response) {
        if (response.status === 400) {
          $(that).parent().html(response.responseText)
          initSelects()
        } else {
          $('.modal-close').click()
        }
      },
      success: function(response) {
        if (response.redirectUrl) {
          window.location.href = response.redirectUrl
        } else {
          location.reload()
        }
      }
    })
    e.preventDefault()
  }).on('click', '.modal-close', function() {
    $('.modal').closeModal()
  })

  function isTablet() {
    return !$('.hide-on-med-only').is(':visible')
  }
})
Dropzone.options.productImageForm = {
  paramName: "image",
  maxFilesize: 20,
  previewsContainer: ".product-gallery",
  thumbnailWidth: 400,
  thumbnailHeight: 250,
  previewTemplate: $("#template").html(),
  clickable: false,
  init: function() {
    var $dropzoneGhost = $('.dropzone-ghost')
    var $gallery = $('.product-gallery')

    this.on('complete', function() {
      $dropzoneGhost.remove().appendTo($gallery)
    }).on('success', function(e, response) {
      $(e.previewElement).find('.product-gallery-item-desc').html(e.name)
      $(e.previewElement).attr('data-id', response.id)
      var editLinkHref = $(e.previewElement).find('.card-action-edit').attr('href')
      editLinkHref = editLinkHref.split('/')
      editLinkHref[editLinkHref.length - 2] = response.id
      $(e.previewElement).find('.card-action-edit').attr('href', editLinkHref.join('/'))
      $(e.previewElement).find('.card-action-edit').show()
      var deleteLinkHref = $(e.previewElement).find('.card-action-delete').attr('data-href')
      deleteLinkHref = deleteLinkHref.split('/')
      deleteLinkHref[deleteLinkHref.length - 3] = response.id
      $(e.previewElement).find('.card-action-delete').attr('data-href', deleteLinkHref.join('/'))
      $(e.previewElement).find('.card-action-delete').show()
      $('.no-images').addClass('hide')
      openModal()
    })
  }
}
var el = document.getElementById('product-gallery')
if (el) {
  Sortable.create(el, {
    handle: '.sortable__handle',
    onUpdate: function () {
      $.ajax({
        dataType: 'json',
        contentType: "application/json",
        data: JSON.stringify({
          'order': (function () {
            var postData = []
            $(el).find('.product-gallery-item[data-id]').each(function() {
              postData.push($(this).data('id'))
            })
            return postData
          })()
        }),
        headers: {
          'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        method: 'post',
        url: $(el).data('post-url')
      })
    }
  })
}
$('.select-all').on('change', function() {
  var $items = $(this).parents('form').find('.switch-actions')
  if (this.checked) {
    $items.prop('checked', true)
  } else {
    $items.prop('checked', false)
  }
})
$('.switch-actions').on('change', function() {
  var $btnChecked = $(this).parents('form').find('.btn-show-when-checked')
  var $btnUnchecked = $(this).parents('form').find('.btn-show-when-unchecked')
  if($(this).parents('form').find('.switch-actions:checked').length) {
    $btnChecked.show()
    $btnUnchecked.hide()
  } else {
    $btnUnchecked.show()
    $btnChecked.hide()
  }
})
$('.datepicker').pickadate({
  format: 'd mmmm yyyy',
  formatSubmit: 'yyyy-mm-dd',
  selectMonths: true,
  hiddenName: true,
  onClose: function() {
    $(document.activeElement).blur();
  }
})
function initSelects() {
  $('select:not(.browser-default):not([multiple])').material_select()
  $('select[multiple]:not(.browser-default)').select2()
}

// Coupon dynamic forms
$(document).ready(() => {
  let $voucherTypeInput = $('.body-vouchers [name="type"]')
  if ($voucherTypeInput.length) {
    let $discountValueType = $('[name="discount_value_type"]')
    let $voucherForms = $('.voucher-form')
    let $applyToProduct = $('[name="product-apply_to"]').parents('.input')
    let $applyToCategory = $('[name="category-apply_to"]').parents('.input')
    let onChange = () => {
      let discountValueType = $discountValueType.val()
      let type = $voucherTypeInput.val()
      let hide = discountValueType === 'percentage'
      $applyToProduct.toggleClass('hide', hide)
      $applyToCategory.toggleClass('hide', hide)

      $voucherForms.each((index, form) => {
        let $form = $(form)
        let hideForm = $form.data('type') !== type
        $form.toggleClass('hide', hideForm)
      })
    }

    $discountValueType.on('change', onChange)
    $voucherTypeInput.on('change', onChange)
    $voucherTypeInput.trigger('change')
  }
})
