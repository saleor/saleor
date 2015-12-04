/* @flow */

import { combineReducers } from 'redux'

import cart from './cart';
import address from './address';

const rootReducer = combineReducers({
  address,
  cart
});

export default rootReducer;
