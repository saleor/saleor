import * as React from 'react';
import * as Relay from 'react-relay';

import ProductPrice from './ProductPrice';

type ProductItemProps = {
  product: any
};

class ProductItem extends React.Component<ProductItemProps, {}> {

  render() {
    const { product } = this.props;
    return (
      <div className="col-6 col-md-4 product-list" itemScope itemType="https://schema.org/Product">
        <a itemProp="url" href={product.url}>
          <div className="text-center">
            <div>
                <img itemProp="image" className="img-responsive" src={product.thumbnailUrl} alt="" />
                <span className="product-list-item-name" itemProp="name" title={product.name}>{product.name}</span>
            </div>
            <div className="panel-footer">
              <ProductPrice price={product.price} availability={product.availability} />
            </div>
          </div>
        </a>
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
          currency
          gross
          grossLocalized
          net
        }
        availability {
          ${ProductPrice.getFragment('availability')}
        }
        thumbnailUrl
        url
      }
    `
  }
});
