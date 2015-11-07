/* @flow */

import {createStore} from 'redux';

function updateCart(state = {total: 'N/A', subtotals: {}}, action) {
  switch(action.type) {
    case ('UPDATE_TOTAL'):
      return {...state, total: action.total};
    case ('UPDATE_SUBTOTAL'):
      let {productId, subtotal} = action;
      let subtotals = {...state.subtotals};
      subtotals[productId] = subtotal;
      return {...state, subtotals};
    default:
      return state;
  }
}

let store = createStore(updateCart);

export default store;
