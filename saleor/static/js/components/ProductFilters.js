import React, { Component, findDOMNode, PropTypes } from 'react'


export default class ProductFilters extends Component {

	static propTypes = {
		categories: PropTypes.object,
		attributes: PropTypes.array
	};

	render() {

		const categoryName = this.props.categories.name;
		const subCategories  = this.props.categories.children.edges;
		const { attributes } = this.props;

		return (
			<div>
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
						<ul className="attributes list-group" key={attribute.id}>
							<li className="list-group-item active">
								{attribute.name}
							</li>
							{attribute.values.map((value) => {
								return (
									<li key={value.id} className="list-group-item">
										{value.display}
									</li>
								)
							})}
						</ul>
					)
				})
				) : (null)}
			</div>
		)
	}
}