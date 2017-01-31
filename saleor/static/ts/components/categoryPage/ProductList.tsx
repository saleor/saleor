import * as React from 'react';
import * as Relay from 'react-relay';

import ProductItem from './ProductItem';
import NoResults from './NoResults';

type ProductListProps = {
  onLoadMore: () => any,
  products: any,
  setSorting: any
};


class ProductList extends React.Component<ProductListProps, {}> {
  onLoadMore = () => this.props.onLoadMore();
  setSorting = (event) => this.props.setSorting(event);

  render() {
    const { edges, pageInfo: { hasNextPage } } = this.props.products;
    return (
      <div>
        <div className="row">
          {edges.length > 0 ? (edges.map((edge, i) => (
            <ProductItem key={i} product={edge.node} />
          ))) : (<NoResults />)}
        </div>
        <div className="load-more">
          {hasNextPage && (
            <button className="btn" onClick={this.onLoadMore}>{gettext('Load more')}</button>
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
    `
  }
});
