import React, {Component, PropTypes} from 'react';
import InlineSVG from 'react-inlinesvg';
import {gql} from 'react-apollo';

import SaleImg from '../../../images/sale_bg.svg';


class ProductPrice extends Component {
  constructor(props) {
    super(props);
  }

  static propTypes = {
    availability: PropTypes.object.isRequired,
    price: PropTypes.object.isRequired
  };

  static fragments = {
    availability: gql`
      fragment ProductPriceFragmentQuery on ProductAvailabilityType {
        available
        discount { 
          gross 
        }
        priceRange {
          maxPrice {
            gross
            grossLocalized
            currency
          }
          minPrice {
            gross
            grossLocalized
            currency
          }
        }
      }
    `
  };

  render() {
    const {discount, priceRange} = this.props.availability;
    const isPriceRange = priceRange && priceRange.minPrice.gross !== priceRange.maxPrice.gross;
    return (
      <div>
      <span itemProp="price">
        {isPriceRange && <span>{pgettext('product price range', 'from')} </span>} {priceRange.minPrice.grossLocalized}
      </span>
        {discount && (
          <div className="product-list__sale"><InlineSVG src={SaleImg}/><span
            className="product-list__sale__text">{pgettext('Sale (discount) label for item in product list', 'Sale')}</span>
          </div>
        )}
      </div>
    );
  }
}

export default ProductPrice;
