import React, { Component, PropTypes } from 'react'


export default class AttributeSelectionWidget extends Component {

  static propTypes = {
    attribute: PropTypes.object.isRequired,
    handleChange: PropTypes.func.isRequired,
    selected: PropTypes.string
  };

  handleChange = (event) => {
    const { name, value } = event.target
    this.props.handleChange(name, value)
  }

  render() {
    const { attribute: { display, pk, values }, selected } = this.props
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
                  defaultChecked={selected === value.pk.toString()}
                  type="radio"
                  value={value.pk}
                />
                {value.display}
              </label>
            )
          })}
        </div>
      </div>
    )
  }
}
