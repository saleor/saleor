import React, { Component, PropTypes } from 'react'

import ProductList from './ProductList'
import ProductFilters from './ProductFilters'


export default class CategoryPage extends Component {

	static propTypes = {
		data: PropTypes.object,
	}

	render() {

		const category = this.props.data.category;
		const products = this.props.data.category.products.edges;
		const attributes = this.props.data.attributes;

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