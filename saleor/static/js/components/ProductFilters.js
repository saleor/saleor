import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay';


class ProductFilters extends Component {

	static propTypes = {
		attributes: PropTypes.array,
		categories: PropTypes.object,
		onFilterChanged: PropTypes.func.isRequired
	};

	constructor(props) {
    super(props);
    this.state = {
			filters: {}
		};
  }

	onClick = (attribute, value, event) => {
		const attrValue = `${attribute}:${value}`;
		const element = event.target;
		this.setState({
			filters: Object.assign(
				this.state.filters,
				{[attrValue]: !this.state.filters[attrValue]})
		});
		const enabled = Object.keys(this.state.filters).filter(key => this.state.filters[key] === true);
		this.props.onFilterChanged(enabled);
		if (element.classList.contains("active")) {
			element.classList.remove("active");
		} else {
			element.classList.add("active");
		}
		
	}

	render() {
		const categoryName = this.props.categories.name;
		const subCategories  = this.props.categories.children.edges;
		const { attributes } = this.props;

		return (
			<div className="product-filters">
				<h2>Filters:</h2>
				<ul className="categories list-group">
					<li className="list-group-item active">{categoryName}</li>
					{subCategories && (subCategories.map((item) => {
							const category = item.node;
							return (
								<li key={category.id} className="list-group-item"><a href={category.url}>{category.name}</a></li>
							);
						})
					)}
				</ul>
				{attributes && (attributes.map((attribute) => {
					return (
						<div key={attribute.id} className="attribute">
							<ul className={attribute.name}>
								<h3>{attribute.display}</h3>
								{attribute.values.map((value) => {
									const colorStyle = {
										backgroundColor: value.color
									}
									return (
										<button key={value.id} className="item" style={colorStyle} onClick={(event) => this.onClick(attribute.pk, value.pk, event)}>
											{value.display}
										</button>
									)
								})}
							</ul>
						</div>
					)
				})
				)}
			</div>
		)
	}
}

export default Relay.createContainer(ProductFilters, {
  fragments: {
    attributes: () => Relay.QL`
      fragment on ProductAttributeType @relay(plural: true) {
	      id
				pk
	      name
	      display
	      values {
	        id
					pk
	        display
	        color
	      }
      }
    `,
  },
});
