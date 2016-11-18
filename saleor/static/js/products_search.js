import $ from 'jquery'
import React from 'react'
import ReactDOM from 'react-dom'

import { ProductList } from './components/products'

class ProductSearch {

	constructor() {
		this.props = {
			className: 'btn class',
			color: ''
		}
		this.renderProducts();
	}

	attachOnclickEvents() {
		$('.fetch_data').on( 'click', (e) => {
			this.props.color = $(e.target).data('color');
			this.renderProducts();
		});
	}

	renderProducts() {
		ReactDOM.render(
			<ProductList {...this.props}/>, document.getElementById('productList')
		);
	}

}

$(document).ready(() => {
	let products = new ProductSearch();
	products.attachOnclickEvents();
});






