import React, { Component, findDOMNode, PropTypes } from 'react'

export class ProductList extends Component {

	static propTypes = {
		className: PropTypes.string,
		categoryId: PropTypes.number,
		color: PropTypes.array,
		size: PropTypes.array,
		minPrice: PropTypes.number,
		maxPrice: PropTypes.number
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
                    	<div key={product.id} className="col-xs-12 col-sm-6 col-md-4 col-lg-3" itemScope itemType="https://schema.org/Product">
                			<div className="panel panel-default text-center">
        						<div className="panel-body">
        							<a itemProp="url" href={product.url}>
        								<img itemProp="image" className="img-responsive" src={product.image_url} alt="" />
        								<span className="product-list-item-name" itemProp="name" title={product.name}>{product.name}</span>
        							</a>
        						</div>
        						<div className="panel-footer">
        							<span itemProp="price">
        								{product.price_value}
        								<span className="currency"> {product.price_currency}</span>
        							</span>
        						</div>
         					</div>
                       	</div>
                    );
                })}
			</div>
		)
	}
}
