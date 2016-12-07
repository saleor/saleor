import React, { Component, PropTypes } from 'react'


export default class CategoryFilter extends Component {

  static propTypes = {
    category: PropTypes.object.isRequired
  }

  render() {
    const { category } = this.props;
    return (
      <ul className="categories list-group">
        <li className="list-group-item active">{category.name}</li>
        {category.children && (category.children.map((subcategory) => {
            return (
              <li key={subcategory.pk} className="list-group-item"><a href={subcategory.url}>{subcategory.name}</a></li>
            );
          })
        )}
      </ul>
    );
  }
}
