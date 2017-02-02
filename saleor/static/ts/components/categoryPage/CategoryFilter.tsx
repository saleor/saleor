import * as React from 'react';

interface CategoryFilterProps {
  category: any;
};

export default class CategoryFilter extends React.Component<CategoryFilterProps, {}> {
  render() {
    const { category } = this.props;
    const parent = category.ancestors ? category.ancestors[category.ancestors.length - 1] : null;
    return (
      <div className="categories">
        <h2><strong>{category.name}</strong></h2>
        {parent && (
          <div className="parents">
            <i className="fa fa-arrow-left" aria-hidden="true"></i>
            <a href={parent.url}>{`${gettext('See all')} ${parent.name}`}</a>
          </div>
        )}
        <ul className={category.parent ? ('childs') : ('childs no-parent')}>
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
