import classNames from 'classnames';
import * as React from 'react';

type QuantityInputProps = {
  errors?: [any],
  handleChange: (event: any) => any,
  quantity: number
};

export default class QuantityInput extends React.Component<QuantityInputProps, {}> {
  render() {
    const { errors, quantity } = this.props;
    const formGroupClasses = classNames({
      'form-group': true,
      'has-error': errors && !!errors.length,
      'product__info__quantity': true
    });
    return (
      <div className={formGroupClasses}>
        <label className="control-label product__variant-picker__label" htmlFor="id_quantity">{gettext('Quantity')}</label>
        <input
          className="form-control"
          defaultValue={quantity.toString()}
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
