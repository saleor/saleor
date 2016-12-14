import queryString from 'query-string';
import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import AttributeInput from './AttributeInput';


class ProductFilters extends Component {

  static propTypes = {
    attributes: PropTypes.array,
    onFilterChanged: PropTypes.func.isRequired,
    urlParams: PropTypes.func.isRequired
  };

  constructor(props) {
    super(props);
    let initialState = {};
    props.attributes.forEach(attribute => {
      attribute.values.forEach(value => {
        initialState[this.getFilterKey(attribute.name, value.slug)] = false;
      });
    });
    this.state = initialState;
  }

  getFilterKey(attributeName, valueSlug) {
    // Returns a key that identifies a filter in the state.
    return `${attributeName}:${valueSlug}`;
  }

  filterChangedCallback() {
    const checked = Object.keys(this.state).filter(
      key => this.state[key] === true);
    this.props.onFilterChanged(checked);
  }

  onClick = (name, value) => {
    this.toggleFilter(name, value);
    this.filterChangedCallback();
  };

  toggleFilter(attributeName, valueSlug) {
    const key = this.getFilterKey(attributeName, valueSlug);
    if (key in this.state) {
      this.setState(Object.assign(this.state, {[key]: !this.state[key]}));
    }
  }

  componentDidMount() {
    let urlParams = queryString.parse(location.search);
    Object.keys(urlParams).map((attributeName) => {
      if (Array.isArray(urlParams[attributeName])) {
        const values = urlParams[attributeName];
        values.map((valueSlug) => {
          this.toggleFilter(attributeName, valueSlug);
        });
      } else {
        const valueSlug = urlParams[attributeName];
        this.toggleFilter(attributeName, valueSlug);
      }
    });
    this.filterChangedCallback();
  }

  render() {
    const { attributes } = this.props;
    return (
      <div className="attributes">
        {attributes && (attributes.map((attribute) => {
          return (
            <div key={attribute.id} className={attribute.name}>
              <ul>
                <h3>{attribute.display}</h3>
                {attribute.values.map((value) => {
                  const key = this.getFilterKey(attribute.name, value.slug);
                  const checked = this.state[key];
                  return (
                    <li key={value.id} className="item">
                      <AttributeInput
                        attribute={attribute}
                        checked={checked}
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
