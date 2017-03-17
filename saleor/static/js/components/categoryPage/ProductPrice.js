import React, { PropTypes } from 'react';
import Relay from 'react-relay';
import InlineSVG from 'react-inlinesvg';

import SaleImg from '../../../images/sale_bg.svg';

const ProductPrice = ({ availability, price }) => {
  const { discount, priceRange } = availability;
  const isPriceRange = priceRange && priceRange.minPrice.gross !== priceRange.maxPrice.gross;
  return (
    <div>
      <span itemProp="price">
        {isPriceRange && <span>{pgettext('product price range', 'from')} </span>} {priceRange.minPrice.grossLocalized}
      </span>
      {discount && (
        <div className="product-list__sale"><InlineSVG src={SaleImg} /><span className="product-list__sale__text">{pgettext('Sale (discount) label for item in product list', 'Sale')}</span></div>
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
