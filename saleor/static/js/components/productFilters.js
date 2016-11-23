import React, { Component, findDOMNode, PropTypes } from 'react'

import { ProductList } from './productList'

export class ProductFilters extends Component {

	render() {
		return(
			<div>
				<button className="btn btn-danger">Red</button>
            	<button className="btn btn-success">Green</button>
            	<button className="btn btn-default">Cancel</button>
			</div>
		)

	}

}