import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay'
import ProductList from './ProductList'
import ProductFilters from './ProductFilters'


class CategoryPage extends Component {

	static propTypes = {
		category: PropTypes.object,
		attributes: PropTypes.array
	}

	render() {
		const category = this.props.category;
		const attributes = this.props.attributes;
		const products = this.props.category.products;

		return (
			<div className="row">
				<div className="col-md-3">
					<ProductFilters categories={category} attributes={attributes} />
				</div>
				<div className="col-md-9">
					<div className="row">
						<ProductList products={products} />
					</div>
				</div>		
			</div>
		)
	}
}

export default Relay.createContainer(CategoryPage, {
  fragments: {
    category: () => Relay.QL`
      fragment on CategoryType {
        id,
        name,
        children(first: 20) {
          edges {
            node {
              id,
              name,
              slug
            }
          }
        }
        products (first: 20) {
          ${ProductList.getFragment('products')}
        }
      }
    `,
  },
});
