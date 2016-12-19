import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import ProductItem from './ProductItem';


class ProductList extends Component {

  static propTypes = {
    onLoadMore: PropTypes.func.isRequired,
    orderBy: PropTypes.func,
    products: PropTypes.object
  };

  onLoadMore = () => this.props.onLoadMore();
  orderBy = (event) => this.props.orderBy(event);

  render() {
    const { edges, pageInfo: { hasNextPage } } = this.props.products;
    return (
      <div>
        <div className="sort-by">
            <button className="btn btn-link">
              <span>Sort by: <strong>Price</strong></span>
              <span className="caret">+</span>
            </button>
            <ul className="sort-list">
              <li className="name">
                <div className="row">
                  <div className="col-md-6">Name:</div>
                  <div className="col-md-6">
                    <span className="name" onClick={this.orderBy}>ascending</span>
                  </div>
                </div>
                <div className="row">
                  <div className="col-md-6"></div>
                  <div className="col-md-6">
                    <span className="-name" onClick={this.orderBy}>descending</span>
                  </div>
                </div>
              </li>
              <li className="price">
                <div className="row">
                  <div className="col-md-6">Price:</div>
                  <div className="col-md-6">
                    <span className="price" onClick={this.orderBy}>ascending</span>
                  </div>
                </div>
                <div className="row">
                  <div className="col-md-6"></div>
                  <div className="col-md-6">
                    <span className="-price" onClick={this.orderBy}>descending</span>
                  </div>
                </div>    
              </li>
            </ul>
        </div>
        <div>
          {edges && (edges.map((edge, i) => (
            <ProductItem key={i} product={edge.node} />
          )))}
        </div>
        <div className="load-more">
          {hasNextPage && (
            <button className="btn" onClick={this.onLoadMore}>Load more</button>
          )}
        </div>
      </div>
    );
  }
}

export default Relay.createContainer(ProductList, {
  fragments: {
    products: () => Relay.QL`
      fragment on ProductTypeConnection {
        edges {
          node {
            ${ProductItem.getFragment('product')}
          }
        }
        pageInfo {
          hasNextPage
        }
      }
    `,
  },
});
