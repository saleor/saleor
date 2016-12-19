import React, { Component } from 'react';

import AttributeSelectionWidget from './AttributeSelectionWidget';


export default class VariantPicker extends Component {

  submit = () => {}

  render() {
    return (
      <div>
        <AttributeSelectionWidget name="Size" />
        <AttributeSelectionWidget name="Color" />
        <div className="form-group">
          <label className="control-label" htmlFor="id_quantity">Quantity</label>
          <input className="form-control" id="id_quantity" max="999" min="0" name="quantity" type="number" value="1" />
        </div>
        <div className="form-group">
          <button className="btn btn-lg btn-block btn-primary" onClick={this.submit}>
            Add to cart
          </button>
        </div>
      </div>
    );
  }
}
