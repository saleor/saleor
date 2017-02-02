import * as React from 'react';
import classNames from 'classnames';

interface AttributeSelectionWidgetProps {
  attribute: any;
  handleChange(attributeId: string, optionId: string): any;
  selected?: string;
};

export default class AttributeSelectionWidget extends React.Component<AttributeSelectionWidgetProps, {}> {
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
