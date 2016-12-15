import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import AttributeInput from './AttributeInput';


class ProductFilters extends Component {

  static propTypes = {
    attributes: PropTypes.array,
    checkedAttributes: PropTypes.array,
    onFilterChanged: PropTypes.func.isRequired
  };

  getFilterKey(attributeName, valueSlug) {
    return `${attributeName}:${valueSlug}`;
  }

  onClick = (attributeName, valueSlug) => {
    this.props.onFilterChanged(this.getFilterKey(attributeName, valueSlug));
  };

  render() {
    const { attributes, checkedAttributes } = this.props;
    return (
      <div className="attributes">
        {attributes && (attributes.map((attribute) => {
          return (
            <div key={attribute.id} className={attribute.name}>
              <ul>
                <h3>{attribute.display}</h3>
                {attribute.values.map((value) => {
                  const key = this.getFilterKey(attribute.name, value.slug);
                  return (
                    <li key={value.id} className="item">
                      <AttributeInput
                        attribute={attribute}
                        checked={checkedAttributes.includes(key)}
                        onClick={this.onClick}
                        value={value}
                      />
                    </li>
                  );
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
    `,
  },
});
