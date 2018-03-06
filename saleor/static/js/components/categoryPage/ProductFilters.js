import React, { Component, PropTypes } from 'react';
import {gql} from 'react-apollo';

import AttributeInput from './AttributeInput';
import FilterHeader from './FilterHeader';
import {isMobile} from '../utils';

class ProductFilters extends Component {

  constructor(props) {
    super(props);
    this.state = {
      visibility: {}
    };
  }

  static propTypes = {
    attributes: PropTypes.array,
    checkedAttributes: PropTypes.array,
    onFilterChanged: PropTypes.func.isRequired
  };

  getFilterKey(attributeSlug, valueSlug) {
    return `${attributeSlug}:${valueSlug}`;
  }

  onClick = (attributeSlug, valueSlug) => {
    this.props.onFilterChanged(this.getFilterKey(attributeSlug, valueSlug));
  };

  changeVisibility = (target) => {
    this.setState({
      visibility: Object.assign(this.state.visibility, {[target]: !this.state.visibility[target]})
    });
  };

  componentWillMount() {
    this.props.attributes.edges.map((node) => {
      let attribute = node.node;
      const attrValue = `${attribute.slug}`;
      this.setState({
        visibility: Object.assign(this.state.visibility, {[attrValue]: !isMobile()})
      });
    });
  }

  static fragments = {
    attributes: gql`
      fragment ProductFiltersFragmentQuery on ProductAttribute {
        id
        name
        slug
        values {
          id
          name
          slug
          color
        }
      }
    `
  };

  render() {
    const { attributes, checkedAttributes } = this.props;
    const { visibility } = this.state;
    return (
      <div className="product-filters__attributes">
        {attributes && (attributes.edges.map((node) => {
          let attribute = node.node;
          return (
            <div key={attribute.id}>
              <FilterHeader
                onClick={() => this.changeVisibility(attribute.slug)}
                title={attribute.name}
                visibility={visibility[attribute.slug]}
              />
              <ul id={attribute.slug}>
                {attribute.values.map((value) => {
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
        }))}
      </div>
    );
  }
}

export default ProductFilters;
