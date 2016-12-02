import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay'
class ProductList extends Component {

	static propTypes = {
		products: PropTypes.object
	};

	render() {
		const products = this.props.products.edges;
		return (
			<div>
				{products ? (products.map((item) => {
					const product = item.node;
					return (
						<div key={product.id} className="col-xs-12 col-sm-6 col-md-4 col-lg-3" itemScope itemType="https://schema.org/Product">
							<div className="panel panel-default text-center">
								<div className="panel-body">
									<a itemProp="url" href={product.url}>
										<img itemProp="image" className="img-responsive" src={product.imageUrl} alt="" />
										<span className="product-list-item-name" itemProp="name" title={product.name}>{product.name}</span>
									</a>
								</div>
								<div className="panel-footer">
									<span itemProp="price">
										{product.price.gross} <span className="currency"> {product.price.currency}</span>
									</span>
								</div>
							</div>
						</div>
					);
				})
				) : (null)}
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
	        		id
		            name
		            price {
		              gross
		              net
		              currency
		            }
		            imageUrl
		            url
	        	}
	        }
      }
    `,
  },
});
