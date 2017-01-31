import { observer } from 'mobx-react';
import * as React from 'react';

interface VariantPriceProps {
  availability: any;
  store?: any;
};

@observer
export default class VariantPrice extends React.Component<VariantPriceProps, {}> {
  render() {
    let priceText, priceUndiscountedText, priceLocalCurrency, isDiscount;
    const { availability, store } = this.props;
    const variant = store.variant;
    if (!store.isEmpty) {
      // variant price
      isDiscount = variant.price.gross !== variant.priceUndiscounted.gross;
      priceText = `${variant.price.grossLocalized}`;
      priceUndiscountedText = `${variant.priceUndiscounted.grossLocalized}`;
      if (variant.priceLocalCurrency) {
        priceLocalCurrency = variant.priceLocalCurrency.grossLocalized;
      }
    } else {
      // if there's no variant, fall back to product price
      const { discount, priceRange, priceRangeUndiscounted } = availability;
      isDiscount = discount && !!Object.keys(discount).length;
      priceText = `${priceRange.minPrice.grossLocalized}`;
      priceUndiscountedText = `${priceRangeUndiscounted.minPrice.grossLocalized}`;
      if (availability.priceRangeLocalCurrency) {
        priceLocalCurrency = availability.priceRangeLocalCurrency.minPrice.grossLocalized;
      }
    }
    return (
      <h2 itemProp="offers" className="product__info__price" itemScope itemType="http://schema.org/Offer">
          <span>{priceText}&nbsp;</span>
          {isDiscount && (
            <small className="product__info__price__undiscounted">{priceUndiscountedText}</small>
          )}
          {priceLocalCurrency && (
            <p><small className="text-info">&asymp; {priceLocalCurrency}</small></p>
          )}
      </h2>
    );
  }
}
