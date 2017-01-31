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
    if (!store.isEmpty) {
      // variant price
      isDiscount = variant.price.gross !== variant.priceUndiscounted.gross;
      priceText = `${variant.price.grossLocalized}`;
      priceUndiscountedText = `${variant.priceUndiscounted.grossLocalized}`;
    } else {
      // if there's no variant, fall back to product price
      const { discount, priceRange, priceRangeUndiscounted } = availability;
      isDiscount = discount && !!Object.keys(discount).length;
      priceText = `${priceRange.minPrice.grossLocalized}`;
      priceUndiscountedText = `${priceRangeUndiscounted.minPrice.grossLocalized}`;
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
