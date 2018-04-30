import { observer } from 'mobx-react';
import React, { Component, PropTypes } from 'react';

export default observer(class VariantPrice extends Component {
  static propTypes = {
    availability: PropTypes.object.isRequired,
    store: PropTypes.object,
    displayGrossPrices: PropTypes.bool
  }

  render() {
    let priceText, priceUndiscountedText, priceLocalCurrency, isDiscount;
    const { availability, store, displayGrossPrices } = this.props;
    const variant = store.variant;
    const taxRate = availability.taxRate;
    if (!store.isEmpty) {
      // variant price
      isDiscount = variant.price.gross !== variant.priceUndiscounted.gross;
      if (displayGrossPrices) {
        priceText = `${variant.price.grossLocalized}`;
        priceUndiscountedText = `${variant.priceUndiscounted.grossLocalized}`;
        if (variant.priceLocalCurrency) {
          priceLocalCurrency = variant.priceLocalCurrency.grossLocalized;
        }
      } else {
        priceText = `${variant.price.netLocalized}`;
        priceUndiscountedText = `${variant.priceUndiscounted.netLocalized}`;
        if (variant.priceLocalCurrency) {
          priceLocalCurrency = variant.priceLocalCurrency.netLocalized;
        }
      }
    } else {
      // if there's no variant, fall back to product price
      const { discount, priceRange, priceRangeUndiscounted } = availability;
      isDiscount = discount && !!Object.keys(discount).length;
      if (displayGrossPrices) {
        priceText = `${priceRange.minPrice.grossLocalized}`;
        priceUndiscountedText = `${priceRangeUndiscounted.minPrice.grossLocalized}`;
        if (availability.priceRangeLocalCurrency) {
          priceLocalCurrency = availability.priceRangeLocalCurrency.minPrice.grossLocalized;
        }
      } else {
        priceText = `${priceRange.minPrice.netLocalized}`;
        priceUndiscountedText = `${priceRangeUndiscounted.minPrice.netLocalized}`;
        if (availability.priceRangeLocalCurrency) {
          priceLocalCurrency = availability.priceRangeLocalCurrency.minPrice.netLocalized;
        }
      }
    }
    return (
      <h2 className="product__info__price">
        <span>{priceText}&nbsp;</span>
        {isDiscount && (
          <small className="product__info__price__undiscounted">{priceUndiscountedText}</small>
        )}
        {priceLocalCurrency && (
          <p><small className="text-info">&asymp; {priceLocalCurrency}</small></p>
        )}
        {displayGrossPrices && (
          <small>including {taxRate}% VAT</small>
        )}
        {!displayGrossPrices && (
          <small>excluding {taxRate}% VAT</small>
        )}
      </h2>
    );
  }
});
