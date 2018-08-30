import * as PropTypes from 'prop-types';
import React, { Component } from 'react';
import gql from 'graphql-tag';

import ProductPrice from './ProductPrice';

class ProductItem extends Component {

  static propTypes = {
    product: PropTypes.object
  };

  getSchema = () => {
    const { product } = this.props;
    let data = {
      "@context": "http://schema.org/",
      "@type": "Product",
      "name": product.name,
      "image": product.thumbnailUrl1x,
      "offers": {
        "@type": "Offer",
        "priceCurrency": product.price.currency,
        "price": product.price.amount,
      }
    };
    return JSON.stringify(data);
  };

  static fragments = {
    product: gql`
      fragment ProductFragmentQuery on Product {
        id
        name
        price {
          currency
          amount
          localized
        }
        availability {
          ...ProductPriceFragmentQuery
        }
        thumbnailUrl1x: thumbnailUrl(size: 255)
        thumbnailUrl2x: thumbnailUrl(size: 510)
        url
      }
      ${ProductPrice.fragments.availability}
    `
  };

  render() {
    const { product } = this.props;
    let productSchema = this.getSchema();
    let srcset = product.thumbnailUrl1x + ' 1x, ' + product.thumbnailUrl2x + ' 2x';
    return (
      <div className="col-6 col-md-4 product-list">
        <script type="application/ld+json">{productSchema}</script>
        <a href={product.url} className="link--clean">
          <div className="text-center">
            <div>
              <img className="img-responsive" src={product.thumbnailUrl1x} srcSet={srcset} alt="" />
              <span className="product-list-item-name" title={product.name}>{product.name}</span>
            </div>
            <div className="panel-footer">
              <ProductPrice availability={product.availability} />
            </div>
          </div>
        </a>
      </div>
    );
  }
}

export default ProductItem;
