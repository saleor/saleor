/* @flow */

import { createStore } from 'redux';

type CartState = {
  total: string;
  subtotals: { [key: number]: string };
};

type CartUpdateTotal = {
  type: 'UPDATE_TOTAL';
  total: string
};

type CartUpdateSubtotal = {
  type: 'UPDATE_SUBTOTAL';
  productId: number;
  subtotal: string
};

type CartAction = CartUpdateTotal | CartUpdateSubtotal;

const defaultState: CartState = {
  total: 'N/A',
  subtotals: {}
}

const cart = (state: CartState = defaultState, action: CartAction) => {
  switch(action.type) {
    case ('UPDATE_TOTAL'):
      return {
        ...state,
        total: action.total
      }
    case ('UPDATE_SUBTOTAL'):
      const { productId, subtotal } = action;
      const subtotals = { ...state.subtotals, [productId]: subtotal }
      return {
        ...state,
        subtotals
      }
    default:
      return state
  }
}

export default createStore(cart)
