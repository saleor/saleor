import _ from 'lodash';
import classNames from 'classnames';
import React, { Component, PropTypes } from 'react';

import AttributeSelectionWidget from './AttributeSelectionWidget';


export default class VariantPicker extends Component {

  static propTypes = {
    attributes: PropTypes.array.isRequired,
    variants: PropTypes.array.isRequired
  }

  constructor(props) {
    super(props);
    this.state = {
      quantity: 1,
      selection: {},
      variant: null
    };
  }

  handleAddToCart = () => {}

  handleAttributeChange = (attrId, valueId) => {
    this.setState({
      selection: Object.assign(this.state.selection, { [attrId]: valueId })
    }, () => {
      let matchedVariant = null;
      this.props.variants.forEach(variant => {
        if (_.isEqual(this.state.selection, variant.attributes)) {
          matchedVariant = variant;
        }
      });
      this.setState({variant: matchedVariant});
    });
  }

  handleQuantityChange = (event) => {
    this.setState({quantity: event.target.value});
  }

  render() {
    const { attributes } = this.props;
    const { quantity, variant } = this.state;

    const addToCartBtnClasses = classNames({
      'btn btn-lg btn-block btn-primary': true,
      'disabled': !variant
    });

    return (
      <div>
        {attributes.map((attribute, i) =>
          <AttributeSelectionWidget
            attribute={attribute}
            handleChange={this.handleAttributeChange}
            key={i}
          />
        )}
        <div className="form-group">
          <label className="control-label" htmlFor="id_quantity">Quantity</label>
          <input
            className="form-control"
            id="id_quantity"
            max="999"
            min="0"
            name="quantity"
            onChange={this.handleQuantityChange}
            type="number"
            value={quantity}
          />
        </div>
        <div className="form-group">
          <button
            className={addToCartBtnClasses}
            onClick={this.handleAddToCart}>
            Add to cart
          </button>
        </div>
      </div>
    );
  }
}
