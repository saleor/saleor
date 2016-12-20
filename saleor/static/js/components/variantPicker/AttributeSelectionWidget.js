import React, { Component, PropTypes } from 'react';


export default class AttributeSelectionWidget extends Component {

  static propTypes = {
    attribute: PropTypes.object.isRequired,
    handleChange: PropTypes.func.isRequired
  };

  handleChange = (event) => {
    const { name, value } = event.target;
    this.props.handleChange(name, value);
  }

  render() {
    const { display, pk, values } = this.props.attribute;
    return (
      <div className="form-group">
        <label className="control-label">{display}</label>
          <div className="radio">
          {values.map((value, i) => {
            return (
              <label className="radio-inline" key={i}>
                <input
                  name={pk}
                  onChange={this.handleChange}
                  type="radio"
                  value={value.pk}
                  disabled={false}
                />
                {value.display}
              </label>
            );
          })}
        </div>
      </div>
    );
  }
}
