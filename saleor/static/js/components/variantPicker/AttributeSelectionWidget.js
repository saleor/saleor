import React, { Component, PropTypes } from 'react';


export default class AttributeSelectionWidget extends Component {

  static propTypes = {
    name: PropTypes.string.isRequired
  };

  render() {
    const { name } = this.props;
    return (
      <div className="form-group">
        <label className="control-label">{name}</label>
        <div className="radio">
          <label className="radio-inline"><input type="radio" name="" value="" />Option</label>
        </div>
      </div>
    );
  }
}
