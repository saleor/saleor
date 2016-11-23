import React, { Component, findDOMNode, PropTypes } from 'react'

import { ProductList } from './productList'
import { ProductFilters } from './productFilters'

export class CategoryPage extends Component {

	render() {
		return(
			<div className="row">	
				<div className="col-md-3">
					<ProductFilters />
				</div>
				<div className="col-md-9">
					<div className="row">
						<ProductList />
					</div>
				</div>
			</div>
		)
	}

}