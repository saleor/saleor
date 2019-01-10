import * as PropTypes from 'prop-types';
import React, { Component } from 'react';
import FilterHeader from './FilterHeader';
import { isMobile } from '../utils';

export default class PriceFilter extends Component {
  constructor(props) {
    super(props);
    this.state = {
      visibility: !isMobile()
    };
  }

  static propTypes = {
    minPrice: PropTypes.number,
    maxPrice: PropTypes.number,
    onFilterChanged: PropTypes.func.isRequired,
    onFilterClear: PropTypes.func.isRequired
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
    const { maxPrice, minPrice, onFilterClear } = this.props;
    const { visibility } = this.state;
    return (
      <div className={['filter-section', visibility ? '' : 'filter-section--closed'].join(' ')}>
        <FilterHeader
          onClick={this.changeVisibility}
          title={pgettext('Price filter on category page', 'Price range')}
        />
        {(visibility || minPrice || maxPrice) && (
          <div className="filter-section__content">
            <div className="price-field">
              <input
                className="form-control"
                defaultValue={minPrice}
                min="0"
                onKeyUp={this.checkKey}
                placeholder={pgettext('Price filter on category page', 'from')}
                ref={input => (this.minPriceInput = input)}
                type="number"
              />
              <span className="dash">&#8212;</span>
              <input
                className="form-control"
                defaultValue={maxPrice}
                min="0"
                onKeyUp={this.checkKey}
                placeholder={pgettext('Price filter on category page', 'to')}
                ref={input => (this.maxPriceInput = input)}
                type="number"
              />
              <span className="clear-filters text-uppercase" onClick={onFilterClear}>
                {pgettext('Category page filters', 'Clear filters')}
              </span>
              <button className="btn btn-primary mt-3" onClick={this.updateFilter}>{pgettext('Price filter on category page', 'Update')}</button>
            </div>
          </div>
        )}
      </div>
    );
  }
}
