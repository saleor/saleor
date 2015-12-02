/* @flow */

import {compose, createStore} from 'redux';

function updateAddress(state = {country: null, level1: null, level2: null, level3: null, address1: null, address2: null, firstName: null, lastName: null, organization: null, postcode: null}, action) {
  switch(action.type) {
    case ('SET_COUNTRY'):
      let {country} = action;
      return {...state, country};
    case ('SET_LEVEL1'):
      let {level1} = action;
      return {...state, level1};
    case ('SET_LEVEL2'):
      let {level2} = action;
      return {...state, level2};
    case ('SET_LEVEL3'):
      let {level3} = action;
      return {...state, level3};
    case ('SET_ADDRESS1'):
      let {address1} = action;
      return {...state, address1};
    case ('SET_ADDRESS2'):
      let {address2} = action;
      return {...state, address2};
    case ('SET_FIRST_NAME'):
      let {firstName} = action;
      return {...state, firstName};
    case ('SET_LAST_NAME'):
      let {lastName} = action;
      return {...state, lastName};
    case ('SET_ORGANIZATION'):
      let {organization} = action;
      return {...state, organization};
    case ('SET_POSTCODE'):
      let {postcode} = action;
      return {...state, postcode};
    default:
      return state;
  }
}

let store = createStore(updateAddress);

export default store;
