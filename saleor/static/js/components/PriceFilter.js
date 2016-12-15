import React, { Component, PropTypes } from 'react';

export default class PriceFilter extends Component {

  static propTypes = {
    minPrice: PropTypes.number,
    maxPrice: PropTypes.number,
    onFilterChanged: PropTypes.func.isRequired
  }

  checkKey = (event) => {
    if (event.key === 'Enter') {
      this.updateFilter();
    }
  };

  updateFilter = () => {
    const minPrice = this.minPriceInput.value;
    const maxPrice = this.maxPriceInput.value;
    this.props.onFilterChanged(minPrice, maxPrice);
  }

  render() {
    const { maxPrice, minPrice } = this.props;
    return (
      <div className="price-range">
        <h3>Price range</h3>
        <input
          className="form-control"
          defaultValue={minPrice}
          min="0"
          onKeyUp={this.checkKey}
          placeholder="min"
          ref={input => this.minPriceInput = input}
          type="number"
        />
        <span>&#8212;</span>
        <input
          className="form-control"
          defaultValue={maxPrice}
          min="0"
          onKeyUp={this.checkKey}
          placeholder="max"
          ref={input => this.maxPriceInput = input}
          type="number"
        />
        <button className="btn" onClick={this.updateFilter}>Update</button>
      </div>
    );
  }
}
