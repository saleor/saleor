import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import AttributeInput from './AttributeInput';
import FilterHeader from './FilterHeader';

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
  }

  getFilterKey(attributeName, valueSlug) {
    return `${attributeName}:${valueSlug}`;
  }

  onClick = (attributeName, valueSlug) => {
    this.props.onFilterChanged(this.getFilterKey(attributeName, valueSlug));
  }

  changeVisibility = (target) => {
    this.setState({
      visibility: Object.assign(this.state.visibility, {[target]: !this.state.visibility[target]})
    });
  }

  componentWillMount() {
    this.props.attributes.map((attribute) => {
      const attrValue = `${attribute.name}`;
      if (window.innerWidth <= 700) {
        this.setState({
          visibility: Object.assign(this.state.visibility, {[attrValue]: false})
        });
      } else {
        this.setState({
          visibility: Object.assign(this.state.visibility, {[attrValue]: true})
        });
      }
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
