import React, { Component, PropTypes } from 'react'

import ProductList from './ProductList'


export default class CategoryPage extends Component {

	static propTypes = {
		products: PropTypes.array
	}

	render() {
		const { products } = this.props;
		return (
			<div className="row">	
				<div className="col-md-3">
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