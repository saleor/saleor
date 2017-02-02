import * as React from 'react';
import * as Relay from 'react-relay';

import AttributeInput from './AttributeInput';
import FilterHeader from './FilterHeader';
import { isMobile } from '../utils';

interface ProductFiltersProps {
  attributes: [any];
  checkedAttributes: [any],
  onFilterChanged(filter: string): any
};

interface ProductFiltersState {
  visibility: {};
};

class ProductFilters extends React.Component<ProductFiltersProps, ProductFiltersState> {

  constructor(props) {
    super(props);
    this.state = {
      visibility: {}
    };
  }

  getFilterKey(attributeName, valueSlug) {
    return `${attributeName}:${valueSlug}`;
  }

  onClick = (attributeName, valueSlug) => {
    this.props.onFilterChanged(this.getFilterKey(attributeName, valueSlug));
  }

  changeVisibility = (target) => {
    this.setState({
      visibility: {...this.state.visibility, [target]: !this.state.visibility[target]}
    });
  }

  componentWillMount() {
    this.props.attributes.map((attribute) => {
      const attrValue = `${attribute.name}`;
      this.setState({
        visibility: {...this.state.visibility, [attrValue]: !isMobile()}
      });
    });
  }

  render() {
    const { attributes, checkedAttributes } = this.props;
    const { visibility } = this.state;
    return (
      <div className="attributes">
        {attributes && (attributes.map((attribute) => {
          return (
            <div key={attribute.id}>
              <FilterHeader
                onClick={() => this.changeVisibility(attribute.name)}
                title={attribute.display}
                visibility={visibility[attribute.name]}
              />
              <ul id={attribute.name}>
                {attribute.values.map((value) => {
                  const key = this.getFilterKey(attribute.name, value.slug);
                  const isKeyChecked = checkedAttributes.indexOf(key) > -1;
                  if (visibility[attribute.name] || isKeyChecked) {
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

export default Relay.createContainer(ProductFilters, {
  fragments: {
    attributes: () => Relay.QL`
      fragment on ProductAttributeType @relay(plural: true) {
        id
        pk
        name
        display
        values {
          id
          slug
          display
          color
        }
      }
    `
  }
});
