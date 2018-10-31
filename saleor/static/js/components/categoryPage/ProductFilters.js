import * as PropTypes from 'prop-types';
import React, { Component } from 'react';
import gql from 'graphql-tag';

import AttributeInput from './AttributeInput';
import FilterHeader from './FilterHeader';
import { isMobile } from '../utils';

class ProductFilters extends Component {
  constructor(props) {
    super(props);
    this.state = {
      visibility: {}
    };
  }

  static propTypes = {
    attributes: PropTypes.object,
    checkedAttributes: PropTypes.array,
    onFilterChanged: PropTypes.func.isRequired
  };

  getFilterKey(attributeSlug, valueSlug) {
    return `${attributeSlug}:${valueSlug}`;
  }

  onClick = (attributeSlug, valueSlug) => {
    this.props.onFilterChanged(this.getFilterKey(attributeSlug, valueSlug));
  };

  changeVisibility = target => {
    this.setState({
      visibility: Object.assign(this.state.visibility, {
        [target]: !this.state.visibility[target]
      })
    });
  };

  componentWillMount() {
    this.props.attributes.edges.map(node => {
      let attribute = node.node;
      const attrValue = `${attribute.slug}`;
      this.setState({
        visibility: Object.assign(this.state.visibility, {
          [attrValue]: !isMobile()
        })
      });
    });
  }

  static fragments = {
    attributes: gql`
      fragment ProductFiltersFragmentQuery on Attribute {
        id
        name
        slug
        values {
          id
          name
          slug
        }
      }
    `
  };

  render() {
    const { attributes, checkedAttributes } = this.props;
    const { visibility } = this.state;
    return (
      <div className="product-filters__attributes">
        {attributes &&
          attributes.edges.map(node => {
            let attribute = node.node;
            return (
              <div
                key={attribute.id}
                className={[
                  'filter-section',
                  visibility[attribute.slug] ? '' : 'filter-section--closed'
                ].join(' ')}
              >
                <FilterHeader
                  onClick={() => this.changeVisibility(attribute.slug)}
                  title={attribute.name}
                />
                <ul id={attribute.slug} className="filter-section__content">
                  {attribute.values.map(value => {
                    const key = this.getFilterKey(attribute.slug, value.slug);
                    const isKeyChecked = checkedAttributes.indexOf(key) > -1;
                    if (visibility[attribute.slug] || isKeyChecked) {
                      return (
                        <li key={value.id} className="item">
                          <AttributeInput
                            attribute={attribute}
                            checked={isKeyChecked}
                            onClick={this.onClick}
                            value={value}
                          />
                        </li>
                      );
                    }
                  })}
                </ul>
              </div>
            );
          })}
      </div>
    );
  }
}

export default ProductFilters;
