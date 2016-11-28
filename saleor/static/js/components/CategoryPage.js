import React, { Component, PropTypes } from 'react'

import ProductList from './ProductList'
import ProductFilters from './ProductFilters'


export default class CategoryPage extends Component {

	static propTypes = {
		products: PropTypes.array,
		categories: PropTypes.array,
		categoryName: PropTypes.string
	}

	render() {
		const { products, categories, categoryName } = this.props;
		return (
			<div className="row">	
				<div className="col-md-3">
					<ProductFilters categories={categories} categoryName={categoryName} />
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