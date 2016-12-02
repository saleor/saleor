import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay';


class ProductFilters extends Component {

	static propTypes = {
		categories: PropTypes.object,
		attributes: PropTypes.array
	};

	render() {

		const categoryName = this.props.categories.name;
		const subCategories  = this.props.categories.children.edges;
		const { attributes } = this.props;

		return (
			<div className="product-filters">
				<h2>Filters:</h2>
				<ul className="categories list-group">
					<li className="list-group-item active">{categoryName}</li>
					{subCategories ? (subCategories.map((item) => {
							const category = item.node;
							return (
								<li key={category.id} className="list-group-item"><a href={category.name}>{category.name}</a></li>
							);
						})
					) : (null)}
				</ul>
				{attributes ? (attributes.map((attribute) => {
					return (
						<div key={attribute.id} className="attribute">
							<ul className={attribute.name}>
								<h3>{attribute.display}</h3>
								{attribute.values.map((value) => {
									const colorStyle = {
										backgroundColor: value.color
									}
									return (
										<li key={value.id} className="item" style={colorStyle}>
											{value.display}
										</li>
									)
								})}
							</ul>
						</div>
					)
				})
				) : (null)}
				
			</div>
		)
	}
}

export default Relay.createContainer(ProductFilters, {
  fragments: {
    attributes: () => Relay.QL`
      fragment on ProductAttributeType @relay(plural: true) {
	      id
	      name
	      display
	      values {
	        id
	        display
	        color
	      }
      }
    `,
  },
});





