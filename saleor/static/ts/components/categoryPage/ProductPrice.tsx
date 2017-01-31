import * as React from 'react';
import * as Relay from 'react-relay';

type ProductPriceProps = {
  availability: any,
  price: any
};

const ProductPrice = ({ availability, price }: ProductPriceProps) => {
  const { discount, priceRange } = availability;
  const isPriceRange = priceRange && priceRange.minPrice.gross !== priceRange.maxPrice.gross;
  const gross = isPriceRange ? priceRange.minPrice.grossLocalized : price.grossLocalized;
  return (
    <div>
      <span itemProp="price">
        {isPriceRange && <span>{gettext('from')} </span>} {gross}
      </span>
      {discount && (
        <div className="product-list__sale"><span>Sale</span></div>
      )}
    </div>
  );
};

export default Relay.createContainer(ProductPrice, {
  fragments: {
    availability: () => Relay.QL`
      fragment on ProductAvailabilityType {
        available,
        discount { gross },
        priceRange {
          maxPrice { gross, grossLocalized, currency },
          minPrice { gross, grossLocalized, currency }
        }
      }
    `
  }
});
