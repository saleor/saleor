import classNames from 'classnames';
import React, { Component, PropTypes } from 'react';

export default class QuantityInput extends Component {

  static propTypes = {
    errors: PropTypes.array,
    handleChange: PropTypes.func.isRequired,
    quantity: PropTypes.number.isRequired
  }

  render() {
    const { errors, quantity } = this.props;
    const formGroupClasses = classNames({
      'form-group': true,
      'has-error': errors && !!errors.length,
      'product__info__quantity': true
    });
    return (
      <div className={formGroupClasses}>
        <label className="control-label product__variant-picker__label" htmlFor="id_quantity">{pgettext('Add to cart form field label', 'Quantity')}</label>
        <input
          className="form-control"
          defaultValue={quantity}
          id="id_quantity"
          max="999"
          min="0"
          name="quantity"
          onChange={this.props.handleChange}
          type="number"
        />
        {errors && (
          <span className="help-block">{errors.join(' ')}</span>
        )}
      </div>
    );
  }
}
