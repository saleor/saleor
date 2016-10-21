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
  function openMenu(a) {
    $('#main-nav').animate({
      'left': '250px'
    },a)
    if ($(window).width() < 1650 && $(window).width() > 991) {
      $('main .container, .subheader .nav-wrapper').animate({
        'marginLeft': '250px'
      },a)
    } 
    $('#open-menu').addClass('hide');
    $('#close-menu').removeClass('hide');
    $('.menu-toggle').addClass('fixed');
    $.cookie('openmenu', true);
  }
  $('#open-menu').click(function() {
    openMenu(400)
  })
  $('#close-menu').click(function() {
    $('#main-nav').animate({
      'left': '0'
    })
    if($(window).width() < 1650) {
      $('main .container, .subheader .nav-wrapper').css({
        'margin-left': 'auto'
      })
    }
    $('#close-menu').addClass('hide');
    $('#open-menu').removeClass('hide');
    $('.menu-toggle').removeClass('fixed')
    $.cookie('openmenu', false)
  })
  if ($.cookie('openmenu') == 'true') {
    openMenu(0)
  } else {
    $('#close-menu').click();
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
