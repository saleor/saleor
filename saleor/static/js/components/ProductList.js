import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay'

import ProductItem from './ProductItem';


class ProductList extends Component {

	static propTypes = {
		products: PropTypes.object
	};

	render() {
		const edges = this.props.products.edges;
		return (
			<div>
				{edges && (edges.map((edge, i) => (
					<ProductItem key={i} product={edge.node} />
				)))}
			</div>
		)
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
      }
    `,
  },
});
