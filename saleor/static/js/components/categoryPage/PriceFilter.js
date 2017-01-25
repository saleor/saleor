import React, { Component, PropTypes } from 'react';
import InlineSVG from 'react-inlinesvg';

import chevronUpIcon from '../../../images/chevron-up-icon.svg';
import chevronDownIcon from '../../../images/chevron-down-icon.svg';

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
    const { minPrice, maxPrice } = this.props;
    if (!(minPrice || maxPrice)) {
      this.setState({
        visibility: !this.state.visibility
      });
    }
  }

  render() {
    const { maxPrice, minPrice } = this.props;
    const { visibility } = this.state;
    const imageSrc = visibility ? (chevronUpIcon) : (chevronDownIcon);
    const key = visibility ? 'chevronUpIcon' : 'chevronDownIcon';
    return (
      <div className="price-range">
        <h3 onClick={this.changeVisibility}>
          Price range
          <div className="collapse-filters-icon">
            <InlineSVG key={key} src={imageSrc} />
          </div>
        </h3>
        {visibility || minPrice || maxPrice ? (
          <div>
            <input
              className="form-control"
              defaultValue={minPrice}
              min="0"
              onKeyUp={this.checkKey}
              placeholder="min"
              ref={input => (this.minPriceInput = input)}
              type="number"
            />
            <span>&#8212;</span>
            <input
              className="form-control"
              defaultValue={maxPrice}
              min="0"
              onKeyUp={this.checkKey}
              placeholder="max"
              ref={input => (this.maxPriceInput = input)}
              type="number"
            />
            <button className="btn" onClick={this.updateFilter}>Update</button>
          </div>
        ) : (null)}
      </div>
    );
  }
}
