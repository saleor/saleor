import React, { Component, PropTypes } from 'react';
import AttributeInput from './AttributeInput';

export default class CategoryFilter extends Component {

  static propTypes = {
    category: PropTypes.object.isRequired
  }

  render() {
    const { category } = this.props;
    return (
      <div className="categories">
        <h3>Categories:</h3>
        <ul>
          <li className="current">
            <a href={category.url}><strong>{category.name}</strong></a>
            <span>{category.productsCount}</span>
          </li>
          {category.children && (category.children.map((child) => {
            return (
              <li key={child.pk} className="item">
                <input
                  name={child.slug}
                  type="checkbox"
                  value={child.slug}
                />
                {child.name}
              </li>
            );
          }))}
        </ul>
      </div>
    );
  }
}
