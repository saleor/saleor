import React, { Component, findDOMNode, PropTypes } from 'react'


export default class ProductFilters extends Component {

	static propTypes = {
		categories: PropTypes.array,
		categoryName: PropTypes.string
	};

	render() {
		const { categories, categoryName } = this.props;
		return(
			<div>
				<h2>Filters:</h2>
				<ul className="categories list-group">
					<li className="list-group-item active">{categoryName}</li>
					{categories.map((item) => {
						const category = item.node;
						return (
							<li key={category.id} className="list-group-item"><a href={category.name}>{category.name}</a></li>
						);
					})}
				</ul>
			</div>
		)
	}
}