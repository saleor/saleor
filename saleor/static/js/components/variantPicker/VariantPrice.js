import { observer } from 'mobx-react';
import React, { Component, PropTypes } from 'react';

@observer
export default class VariantPrice extends Component {

  static propTypes = {
    availability: PropTypes.object.isRequired,
    store: PropTypes.object
  }

  render() {
    let priceText, priceUndiscountedText, isDiscount;
    const { availability, store } = this.props;
    const variant = store.variant;
    const currency = availability.priceRange.minPrice.currency;
    if (!store.isEmpty) {
      // variant price
      isDiscount = variant.price !== variant.priceUndiscounted;
      priceText = `${variant.price} ${currency}`;
      priceUndiscountedText = `${variant.priceUndiscounted} ${currency}`;
    } else {
      // if there's no variant, fall back to product price
      const { discount, priceRange, priceRangeUndiscounted } = availability;
      isDiscount = discount && !!Object.keys(discount).length;
      priceText = `${priceRange.minPrice.gross} ${currency}`;
      priceUndiscountedText = `${priceRangeUndiscounted.minPrice.gross} ${currency}`;
    }
    return (
      <h2 itemProp="offers" className="product__info__price" itemScope itemType="http://schema.org/Offer">
          <span>{priceText}&nbsp;</span>
          {isDiscount && (
            <small className="product__info__price__undiscounted">{priceUndiscountedText}</small>
          )}
      </h2>
    );
  }
}
