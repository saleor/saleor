/* @flow */

import 'bootstrap-sass'
import $ from 'jquery'
import 'jquery.cookie'

import '../scss/storefront.scss'

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

$(function() {
  const $carousel = $('.carousel')
  const $items = $('.product-gallery-item')
  const $modal = $('.modal')

  $items.on('click', function(e) {
    if ($carousel.is(':visible')) {
      e.preventDefault()
    }
    const index = $(this).index()
    $carousel.carousel(index)
  })

  $modal.on('show.bs.modal', function() {
    const $img = $(this).find('.modal-body img')
    const dataSrc = $img.attr('data-src')
    $img.attr('src', dataSrc)
  })
})
