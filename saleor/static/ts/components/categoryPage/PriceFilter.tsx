import * as React from 'react';
import FilterHeader from './FilterHeader';
import {isMobile} from '../utils';

interface PriceFilterProps {
    minPrice: number;
    maxPrice: number;
    onFilterChanged(minPrice: number, maxPrice: number): any;
};

interface PriceFilterState {
  visibility: boolean;
};

export default class PriceFilter extends React.Component<PriceFilterProps, PriceFilterState> {
  minPriceInput: HTMLInputElement;
  maxPriceInput: HTMLInputElement;

  constructor(props) {
    super(props);
      this.state = {
        visibility: !isMobile()
      };
  }

  checkKey = (event) => {
    if (event.key === 'Enter') {
      this.updateFilter();
    }
  }

  updateFilter = () => {
    const minPrice = parseFloat(this.minPriceInput.value);
    const maxPrice = parseFloat(this.maxPriceInput.value);
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
    return (
      <div className="price-range">
        <FilterHeader
          onClick={this.changeVisibility}
          title={gettext('Price range')}
          visibility={visibility}
        />
        {visibility && (
          <div>
            <input
              className="form-control"
              defaultValue={minPrice.toString()}
              min="0"
              onKeyUp={this.checkKey}
              placeholder={gettext('from')}
              ref={input => (this.minPriceInput = input)}
              type="number"
            />
            <span>&#8212;</span>
            <input
              className="form-control"
              defaultValue={maxPrice.toString()}
              min="0"
              onKeyUp={this.checkKey}
              placeholder={gettext('to')}
              ref={input => (this.maxPriceInput = input)}
              type="number"
            />
            <button className="btn btn-primary" onClick={this.updateFilter}>{gettext('Update')}</button>
          </div>
        )}
      </div>
    );
  }
}
