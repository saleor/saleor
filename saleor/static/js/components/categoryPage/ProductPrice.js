import React, { PropTypes } from 'react';
import Relay from 'react-relay';


const ProductPrice = ({ availability }) => {
  const { discount, priceRange } = availability;
  return (
    <div>
      <span itemProp="price">
        {priceRange.minPrice.gross} <span className="currency"> {priceRange.minPrice.currency}</span>
      </span>
      {discount && (
        <div className="product-list__sale"><span>Sale</span></div>
      )}
    </div>
  );
};


ProductPrice.propTypes = {
  availability: PropTypes.object.isRequired
};


export default Relay.createContainer(ProductPrice, {
  fragments: {
    availability: () => Relay.QL`
      fragment on ProductAvailabilityType {
        available,
        discount { gross },
        priceRange {
          maxPrice { gross, currency },
          minPrice { gross, currency }
        }
      }
    `
  }
});
