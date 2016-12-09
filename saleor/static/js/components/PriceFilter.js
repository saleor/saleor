import React, { Component, PropTypes } from 'react';
import queryString from 'query-string';

export default class PriceFilter extends Component {

  static propTypes = {
    onFilterChanged: PropTypes.func.isRequired,
    urlParams: PropTypes.func.isRequired
  }

  constructor(props) {
    super(props);
    this.state = {
      minPrice: null,
      maxPrice: null,
      filters: []
    }
  }

  checkKey = (event) => {
    if (event.key === 'Enter') {
      this.updateFilter()
    }
  };

  onChange = (event) => {
    const { name, value } = event.target;
    this.setState({[name]: value})
  }

  parseValue = (value) => {
    if (value) {
      try {
        return parseFloat(value);
      } catch (error) {
        return null;
      }
    }
    return null;
  }

  updateFilter = () => {
    let { minPrice, maxPrice } = this.state;
    minPrice = this.parseValue(minPrice);
    maxPrice = this.parseValue(maxPrice);

    this.props.onFilterChanged(minPrice, maxPrice);
  }

  render() {
    return (
      <div className="price-range">
        <h3>Price range</h3>
        <input
          id="minPrice"
          className="form-control"
          name="minPrice"
          onChange={this.onChange}
          onKeyUp={this.checkKey}
          placeholder="min"
          type="number"
          value={this.state.minPrice}
        />
        <span>&#8212;</span>
        <input
          id="maxPrice"
          name="maxPrice"
          className="form-control"
          onChange={this.onChange}
          onKeyUp={this.checkKey}
          placeholder="max"
          type="number"
          value={this.state.maxPrice}
        />
        <button className="btn" onClick={this.updateFilter}>Update</button>
      </div>
    );
  }
}
