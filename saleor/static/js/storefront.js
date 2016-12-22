/* @flow */

import 'bootstrap-sass'
import $ from 'jquery'
import 'jquery.cookie'
import React from 'react'
import ReactDOM from 'react-dom'

import '../scss/storefront.scss'
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


const variantPicker = document.getElementById('variant-picker')
if (variantPicker) {
  const variantPickerData = JSON.parse(variantPicker.dataset.variantPickerData)
  ReactDOM.render(
    <VariantPicker
      attributes={variantPickerData.attributes}
      url={variantPicker.dataset.action}
      variants={variantPickerData.variants}
    />,
    variantPicker
  )

}

