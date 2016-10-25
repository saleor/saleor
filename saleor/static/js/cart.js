/* @flow */

import $ from 'jquery'
import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'

import { CartItemAmount, CartItemSubtotal, CartTotal } from './components/cart'
import store from './stores/cart-store'

import '../scss/cart.scss'

const options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

$('.cart-item-amount').each(function(index) {
  let $input = $(this).find('input')
  let $button = $(this).find('button')
  let value = $input.val()
  let name = $input.attr('name')
  let max = $input.attr('max')
  let props = {
    className: '',
    index: index,
    max: parseInt(max),
    options: options.slice(0, max),
    thresholdValue: options[options.length - 1],
    url: $(this).find('form').attr('action'),
    fieldName: name,
    value: parseInt(value)
  }
  $(this).find('.cart-item-quantity').removeClass('js-hidden')
  $button.addClass('invisible')
  render(
    <Provider store={store}>
      <CartItemAmount {...props}/>
    </Provider>,
    this
  )
})

let $cartTotal = $('.cart-total')
let cartTotalValue = $cartTotal.data('value')
let cartLocalTotalValue = $cartTotal.data('value-local')
if ($cartTotal.length) {
  store.dispatch({
    type: 'UPDATE_TOTAL',
    total: cartTotalValue,
    localTotal: cartLocalTotalValue
  })
  render(
    <Provider store={store}>
      <CartTotal />
    </Provider>,
    $cartTotal[0]
  )
}

$('.cart-item-subtotal').each(function() {
  let productId = $(this).data('product-id')
  let props = {
    productId,
    subtotal: $(this).text()
  }
  store.dispatch({
    type: 'UPDATE_SUBTOTAL',
    ...props
  })
  render(
    <Provider store={store}>
      <CartItemSubtotal productId={productId} />
    </Provider>,
    this
  )
})
