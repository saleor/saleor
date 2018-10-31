import * as PropTypes from 'prop-types';
import React, { Component } from 'react';
import gql from 'graphql-tag';

import ProductItem from './ProductItem';
import NoResults from './NoResults';

class ProductList extends Component {

  static propTypes = {
    onLoadMore: PropTypes.func.isRequired,
    products: PropTypes.object,
    setSorting: PropTypes.object,
    updating: PropTypes.object
  };

  onLoadMore = () => this.props.onLoadMore();

  static fragments = {
    products: gql`
      fragment ProductListFragmentQuery on ProductCountableConnection {
        edges {
          node {
            ...ProductFragmentQuery
          }
        }
        pageInfo {
          hasNextPage
        }
      }
      ${ProductItem.fragments.product}
    `
  };

  render() {
    const { edges, pageInfo: { hasNextPage } } = this.props.products;
    return (
      <div className={this.props.loading ? 'category-list--loading' : ''}>
        <div className="row">
          {edges.length > 0 ? (edges.map((edge, i) => (
            <ProductItem key={i} product={edge.node} />
          ))) : (<NoResults />)}
        </div>
        <div className="load-more">
          {hasNextPage && (
            <button className="btn gray" onClick={this.onLoadMore}>
              {pgettext('Load more products on category view', 'Load more')}
            </button>
          )}
        </div>
      </div>
    );
  }
}

export default ProductList;
