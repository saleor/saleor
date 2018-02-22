import React, { Component } from 'react';
import PropTypes from 'prop-types';
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
      <div className="variant-picker">
        <div className="variant-picker__label">{attribute.name}</div>
        <div className="btn-group" data-toggle="buttons">
          {attribute.values.map((value, i) => {
            const active = selected === value.pk.toString();
            const labelClass = classNames({
              'btn btn-secondary variant-picker__option': true,
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
                {value.name}
              </label>
            );
          })}
        </div>
      </div>
    );
  }
}
