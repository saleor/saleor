/* @flow */

import { createStore } from 'redux';

type CartState = {
  total: string;
  subtotals: { [key: number]: string };
};

type CartUpdateTotal = {
  type: 'UPDATE_TOTAL';
  total: string,
  localTotal: string
};

type CartUpdateSubtotal = {
  type: 'UPDATE_SUBTOTAL';
  variantId: number;
  subtotal: string
};

type CartAction = CartUpdateTotal | CartUpdateSubtotal;

const defaultState: CartState = {
  total: 'N/A',
  localTotal: undefined,
  subtotals: {}
}

const cart = (state: CartState = defaultState, action: CartAction) => {
  switch(action.type) {
    case ('UPDATE_TOTAL'):
      return {
        ...state,
        total: action.total,
        localTotal: action.localTotal
      }
    case ('UPDATE_SUBTOTAL'):
      const { variantId, subtotal } = action;
      const subtotals = { ...state.subtotals, [variantId]: subtotal }
      return {
        ...state,
        subtotals
      }
    default:
      return state
  }
}

export default createStore(cart)
