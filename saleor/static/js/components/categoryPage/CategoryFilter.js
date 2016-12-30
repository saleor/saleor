import React, { Component, PropTypes } from 'react';

export default class CategoryFilter extends Component {

  static propTypes = {
    category: PropTypes.object.isRequired
  }

  render() {
    const { category } = this.props;
    return (
      <div className="categories">

        <h2><strong>{category.name}</strong></h2>

        {category.parent ? (
          <div className="parents">
            <i className="fa fa-arrow-left" aria-hidden="true"></i>
            <a href={category.parent.url}>See all {category.parent.name}</a>
          </div>
        ) : (null)}
        <ul className={category.parent ? ("childs") : ("childs no-parent")}>
          {category.children && (category.children.map((child) => {
            return (
                <li key={child.pk} className="item">
                  <a href={child.url}>{child.name}</a>
                </li>
            );
          }))}
        </ul>
      </div>
    );
  }
}
