import classNames from 'classnames'
import React, { Component, PropTypes } from 'react'


export default class QuantityInput extends Component {

  static propTypes = {
    errors: PropTypes.array,
    handleChange: PropTypes.func.isRequired,
    quantity: PropTypes.number.isRequired
  }

  render() {
    const { errors, quantity } = this.props
    const formGroupClasses = classNames({
      'form-group': true,
      'has-error': errors && !!errors.length
    })
    return (
      <div className={formGroupClasses}>
        <label className="control-label" htmlFor="id_quantity">Quantity</label>
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
    )
  }
}
