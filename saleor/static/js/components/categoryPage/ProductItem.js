import * as PropTypes from "prop-types";
import React, { Component } from "react";
import gql from "graphql-tag";

import ProductPrice from "./ProductPrice";

class ProductItem extends Component {
  static propTypes = {
    product: PropTypes.object
  };

  getSchema = () => {
    const { product } = this.props;
    let data = {
      "@context": "http://schema.org/",
      "@type": "Product",
      name: product.name,
      image: product.thumbnail1x.url,
      offers: {
        "@type": "Offer",
        priceCurrency: product.pricing.priceRange.start.gross.currency,
        price: product.pricing.priceRange.start.gross.amount
      }
    };
    return JSON.stringify(data);
  };

  static fragments = {
    product: gql`
      fragment ProductFragmentQuery on Product {
        id
        name
        pricing {
          ...ProductPriceFragmentQuery
        }
        thumbnail1x: thumbnail(size: 255) {
          url
        }
        thumbnail2x: thumbnail(size: 510) {
          url
        }
        url
      }
      ${ProductPrice.fragments.availability}
    `
  };

  render() {
    const { product } = this.props;
    let productSchema = this.getSchema();
    let srcset =
      product.thumbnail1x.url + " 1x, " + product.thumbnail2x.url + " 2x";
    return (
      <div className="col-6 col-md-4 product-list">
        <script type="application/ld+json">{productSchema}</script>
        <a href={product.url} className="link--clean">
          <div className="text-center">
            <div>
              <img
                className="img-responsive"
                src={product.thumbnail1x.url}
                srcSet={srcset}
                alt=""
              />
              <span className="product-list-item-name" title={product.name}>
                {product.name}
              </span>
            </div>
            <div className="panel-footer">
              <ProductPrice availability={product.pricing} />
            </div>
          </div>
        </a>
      </div>
    );
  }
}

export default ProductItem;
