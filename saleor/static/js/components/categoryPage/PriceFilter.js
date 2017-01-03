import React, { Component, PropTypes } from 'react';

export default class PriceFilter extends Component {

  constructor(props) {
    super(props);
    this.state = {
      visibility: true
    };
  }

  static propTypes = {
    minPrice: PropTypes.number,
    maxPrice: PropTypes.number,
    onFilterChanged: PropTypes.func.isRequired
  }

  checkKey = (event) => {
    if (event.key === 'Enter') {
      this.updateFilter();
    }
  }

  updateFilter = () => {
    const minPrice = this.minPriceInput.value;
    const maxPrice = this.maxPriceInput.value;
    this.props.onFilterChanged(minPrice, maxPrice);
  }

  changeVisibility = () => {
    this.setState({
      visibility: !this.state.visibility
    });
  }

  render() {
    const { maxPrice, minPrice } = this.props;
    const { visibility } = this.state;
    return (
      <div className="price-range">
        <h3 onClick={this.changeVisibility}>
          Price range
          <i className={visibility ? ('fa fa-chevron-up pull-right') : ('fa fa-chevron-down pull-right')} aria-hidden="true"></i>
        </h3>
        {visibility ? (
          <div>
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
        ) : (null)}
      </div>
    );
  }
}
