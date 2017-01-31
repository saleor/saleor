import React, { PropTypes } from 'react';
import Relay from 'react-relay';

const ProductPrice = ({ availability, price }) => {
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

ProductPrice.propTypes = {
  availability: PropTypes.object.isRequired,
  price: PropTypes.object.isRequired
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
