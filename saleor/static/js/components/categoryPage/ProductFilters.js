import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';
import InlineSVG from 'react-inlinesvg';

import AttributeInput from './AttributeInput';

import chevronUpIcon from '../../../images/chevron-up-icon.svg';
import chevronDownIcon from '../../../images/chevron-down-icon.svg';

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
      this.setState({
        visibility: Object.assign(this.state.visibility, {[attrValue]: true})
      });
    });
  }

  render() {
    const { attributes, checkedAttributes } = this.props;
    const { visibility } = this.state;
    return (
      <div className="attributes">
        {attributes && (attributes.map((attribute) => {
          const imageSrc = visibility[attribute.name] ? (chevronUpIcon) : (chevronDownIcon);
          const key = visibility[attribute.name] ? 'chevronUpIcon' : 'chevronDownIcon';
          return (
            <div key={attribute.id}>
              <h3 className={attribute.name} onClick={() => this.changeVisibility(attribute.name)}>
                {attribute.display}
                <div className="collapse-filters-icon">
                  <InlineSVG key={key} src={imageSrc} />
                </div>
              </h3>
              <ul id={attribute.name}>
                {attribute.values.map((value) => {
                  const key = this.getFilterKey(attribute.name, value.slug);
                  if (visibility[attribute.name] || checkedAttributes.includes(key)) {
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
