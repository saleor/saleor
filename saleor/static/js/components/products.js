import React, { Component, findDOMNode, PropTypes } from 'react'
import { connect } from 'react-redux'
import $ from 'jquery'
import axios from 'axios';

export class ProductList extends Component {

	static propTypes = {
		className: PropTypes.string,
		color: PropTypes.string,
	};

	state = {
		data: [],
	};

	componentWillMount() {
		fetch("https://private-58ac5-saleor.apiary-mock.com/products/", {
			method: 'GET',
		}).then(res => {
	        res.json().then((data) => {  
	        this.setState({
	          data: data
	        });
	      });
		});
	}

	componentWillReceiveProps(nextProps) {
		let url = "https://private-58ac5-saleor.apiary-mock.com/products/" + nextProps.color
		fetch(url, {
			method: 'GET',
		}).then(res => {
	        res.json().then((data) => {  
	        this.setState({
	          data: data
	        });
	      });
		});
	}

	render() {

		const { data } = this.state;
		const { color } = this.props;

		return (
			<div>
				{data.map((product) => {
                    return (
                        <p key={product.id}>
                       		<a href={product.url}>{product.name} - {product.price_value} {product.price_currency} - {product.attributes[0].color}</a>
                       	</p>
                    );
                })}
			</div>
		)
	}
}