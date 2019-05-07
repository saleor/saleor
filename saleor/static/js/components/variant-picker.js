import React from 'react';
import ReactDOM from 'react-dom';

import VariantPicker from './variantPicker/VariantPicker';
import VariantPrice from './variantPicker/VariantPrice';
import variantPickerStore from '../stores/variantPicker';

import {onAddToCheckoutSuccess, onAddToCheckoutError} from './checkout';

export default $(document).ready((e) => {
  const variantPickerContainer = document.getElementById('variant-picker');
  const variantPriceContainer = document.getElementById('variant-price-component');

  if (variantPickerContainer) {
    const variantPickerData = JSON.parse(variantPickerContainer.dataset.variantPickerData);
    ReactDOM.render(
      <VariantPicker
        onAddToCheckoutError={onAddToCheckoutError}
        onAddToCheckoutSuccess={onAddToCheckoutSuccess}
        store={variantPickerStore}
        url={variantPickerContainer.dataset.action}
        variantAttributes={variantPickerData.variantAttributes}
        variants={variantPickerData.variants}
      />,
      variantPickerContainer
    );

    if (variantPriceContainer) {
      ReactDOM.render(
        <VariantPrice
          availability={variantPickerData.availability}
          priceDisplay={variantPickerData.priceDisplay}
          store={variantPickerStore}
        />,
        variantPriceContainer
      );
    }
  }
});
