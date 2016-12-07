import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay'


class ProductItem extends Component {

  static propTypes = {
    product: PropTypes.object
  };

  render() {
    const { product } = this.props;
    return (
      <div className="col-xs-6 col-md-4 product-list" itemScope itemType="https://schema.org/Product">
        <div className="text-center">
          <div>
            <a itemProp="url" href={product.url}>
              <img itemProp="image" className="img-responsive" src={product.imageUrl} alt="" />
              <span className="product-list-item-name" itemProp="name" title={product.name}>{product.name}</span>
            </a>
          </div>
          <div className="panel-footer">
            <span itemProp="price">
              {product.price.gross} <span className="currency"> {product.price.currency}</span>
            </span>
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
        price {
          gross
          net
          currency
        }
        imageUrl
        url
      }
    `,
  },
});
