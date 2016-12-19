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
        <ul className="parents">
          {category.ancestors.map((ancestor) => {
            return (
              <li key={ancestor.pk}><a href={ancestor.url}><strong>{ancestor.name} / </strong></a></li>
            );
          })}
          <li className="current">
            <a href={category.url}><strong>{category.name}</strong></a>
          </li>
        </ul>
        {category.children && (category.children.map((child) => {
          return (
            <ul key={child.pk} className="childs">
              <li className="item">
                <a href={child.url}>{child.name}</a>
              </li>
              {child.children && (child.children.map((child) => {
                return (
                  <ul key={child.pk} className="childs">
                    <li className="item">
                      <a href={child.url}>{child.name}</a>
                    </li>
                  </ul>
                );
              }))}
            </ul>
          );
        }))}
      </div>
    );
  }
}
