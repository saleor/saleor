import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay';

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
            <a href={category.url}>{category.name}</a>
            <span>{category.productsCount}</span>
          </li>
          {category.siblings && (category.siblings.map((sibling) => {
              return (
                <li key={sibling.pk} className="item">
                  <a href={sibling.url}>{sibling.name}</a>
                  <span>{sibling.productsCount}</span>
                </li>
              );
            })
          )}
        </ul>
      </div>
    );
  }
}
