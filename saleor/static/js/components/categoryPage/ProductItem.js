import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import ProductPrice from './ProductPrice';

class ProductItem extends Component {

  static propTypes = {
    product: PropTypes.object
  };

  render() {
    const { product } = this.props;
    return (
      <div className="col-6 col-md-4 product-list" itemScope itemType="https://schema.org/Product">
        <div className="text-center">
          <div>
            <a itemProp="url" href={product.url}>
              <img itemProp="image" className="img-responsive" src={product.thumbnailUrl} alt="" />
              <span className="product-list-item-name" itemProp="name" title={product.name}>{product.name}</span>
            </a>
          </div>
          <div className="panel-footer">
            <ProductPrice availability={product.availability} />
          </div>
        </div>
      </div>
    );
  }
}

export default Relay.createContainer(ProductItem, {
  fragments: {
    product: () => Relay.QL`
      fragment on ProductType {
        id
        name
        availability {
          ${ProductPrice.getFragment('availability')}
        }
        thumbnailUrl
        url
      }
    `
  }
});
