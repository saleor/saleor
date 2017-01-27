import React, { Component, PropTypes } from 'react';
import classNames from 'classnames';

export default class AttributeSelectionWidget extends Component {

  static propTypes = {
    attribute: PropTypes.object.isRequired,
    handleChange: PropTypes.func.isRequired,
    selected: PropTypes.string
  };

  handleChange = (attrPk, valuePk) => {
    this.props.handleChange(attrPk.toString(), valuePk.toString());
  }

  render() {
    const { attribute, selected } = this.props;
    return (
      <div className="product__variant-picker">
        <div className="product__variant-picker__label">{attribute.display}</div>
        <div className="btn-group" data-toggle="buttons">
          {attribute.values.map((value, i) => {
            const active = selected === value.pk.toString();
            const labelClass = classNames({
              'btn btn-secondary': true,
              'active': active
            });
            return (
              <label
                className={labelClass}
                key={i}
                onClick={() => this.handleChange(attribute.pk, value.pk)}>
                <input
                  defaultChecked={active}
                  name={value.pk}
                  type="radio"/>
                {value.display}
              </label>
            );
          })}
        </div>
      </div>
    );
  }
}
