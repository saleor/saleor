import queryString from 'query-string';
import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import CategoryFilter from './CategoryFilter';
import PriceFilter from './PriceFilter';
import ProductFilters from './ProductFilters';
import ProductList from './ProductList';
import SortBy from './SortBy';
import { ensureAllowedName, getAttributesFromQuery, getFromQuery } from './utils';
import {isMobile} from '../utils';

const PAGINATE_BY = 24;
const SORT_BY_FIELDS = ['name', 'price'];

class CategoryPage extends Component {

  constructor(props) {
    super(props);
    this.state = {
      filtersMenu: !isMobile()
    };
  }

  static propTypes = {
    attributes: PropTypes.array,
    category: PropTypes.object,
    relay: PropTypes.object
  }

  incrementProductsCount = () => {
    this.props.relay.setVariables({
      count: this.props.relay.variables.count + PAGINATE_BY
    });
  }

  setSorting = (value) => {
    this.props.relay.setVariables({
      sortBy: value
    });
  }

  toggleMenu = (target) => {
    this.setState({
      filtersMenu: !target
    });
  }

  clearFilters = () => {
    this.props.relay.setVariables({ 
      attributesFilter: [],
      minPrice: null,
      maxPrice: null 
    });
  }

  updateAttributesFilter = (key) => {
    // Create a new attributesFilter array by cloning the current one to make
    // Relay refetch products with new attributes. Passing the same array (even
    // if it's modified) would not result in new query, but would return cached
    // results.
    const attributesFilter = this.props.relay.variables.attributesFilter.slice(0);
    const index = attributesFilter.indexOf(key);
    if (index < 0) {
      attributesFilter.push(key);
    } else {
      attributesFilter.splice(index, 1);
    }
    this.props.relay.setVariables({ attributesFilter });
  }

  updatePriceFilter = (minPrice, maxPrice) => {
    this.props.relay.setVariables({
      minPrice: parseInt(minPrice) || null,
      maxPrice: parseInt(maxPrice) || null
    });
  }

  persistStateInUrl() {
    const { attributesFilter, count, maxPrice, minPrice, sortBy } = this.props.relay.variables;
    let urlParams = {};
    if (minPrice) {
      urlParams['minPrice'] = minPrice;
    }
    if (maxPrice) {
      urlParams['maxPrice'] = maxPrice;
    }
    if (count > PAGINATE_BY) {
      urlParams['count'] = count;
    }
    if (sortBy) {
      urlParams['sortBy'] = sortBy;
    }
    attributesFilter.forEach(filter => {
      const [ attributeName, valueSlug ] = filter.split(':');
      if (attributeName in urlParams) {
        urlParams[attributeName].push(valueSlug);
      } else {
        urlParams[attributeName] = [valueSlug];
      }
    });
    const url = Object.keys(urlParams).length ? '?' + queryString.stringify(urlParams) : location.href.split('?')[0];
    history.pushState({}, null, url);
  }

  componentDidUpdate() {
    // Persist current state of relay variables as query string. Current
    // variables are available in props after component rerenders, so it has to
    // be called inside componentDidUpdate method.
    this.persistStateInUrl();
  }

  render() {
    const { attributes, category, relay: { variables }, relay } = this.props;
    const { pendingVariables } = relay;
    const { filtersMenu } = this.state;
    return (
      <div className="category-page">
        <div className="category-top">
          <div className="row">
            <div className="col-md-7">
              <ul className="breadcrumbs list-unstyled hidden-sm-down">
                <li><a href="/">{pgettext('Main navigation item', 'Home')}</a></li>
                  {category.ancestors && (category.ancestors.map((ancestor) => {
                    return (
                      <li key={ancestor.pk}><a href={ancestor.url}>{ancestor.name}</a></li>
                    );
                  }))}
                <li><a href={category.url}>{category.name}</a></li>
              </ul>
            </div>
            <div className="col-md-5">
              <div className="row">
                <div className="col-6 col-md-2 col-lg-6 filters-menu">
                  <span className="filters-menu__label hidden-sm-up" onClick={() => this.toggleMenu(filtersMenu)}>{pgettext('Category page filters', 'Filters')}</span>
                  {(variables.attributesFilter.length || variables.minPrice || variables.maxPrice) && (
                    <span className="filters-menu__icon hidden-sm-up"></span>
                  )}
                </div>
                <div className="col-6 col-md-10 col-lg-6">
                  <SortBy sortedValue={variables.sortBy} setSorting={this.setSorting} />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="row">
          <div className="col-md-4 col-lg-3">
            <div className="product-filters">
              <CategoryFilter category={category} />
            </div>
            {filtersMenu && (
            <div>
              <h2>
                {pgettext('Category page filters', 'Filters')}
                <span className="clear-filters float-right" onClick={this.clearFilters}>{pgettext('Category page filters', 'Clear filters')}</span>
              </h2>
              <div className="product-filters">
                <ProductFilters
                  attributes={attributes}
                  checkedAttributes={variables.attributesFilter}
                  onFilterChanged={this.updateAttributesFilter}
                />
                <PriceFilter
                  onFilterChanged={this.updatePriceFilter}
                  maxPrice={variables.maxPrice}
                  minPrice={variables.minPrice}
                />
              </div>
            </div>
            )}
          </div>
          <div className="col-md-8 col-lg-9 category-list">
            <div>
              <ProductList
                onLoadMore={this.incrementProductsCount}
                products={category.products}
                updating={pendingVariables}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default Relay.createContainer(CategoryPage, {
  initialVariables: {
    attributesFilter: getAttributesFromQuery(['count', 'minPrice', 'maxPrice', 'sortBy']),
    count: parseInt(getFromQuery('count', PAGINATE_BY)) || PAGINATE_BY,
    minPrice: parseInt(getFromQuery('minPrice')) || null,
    maxPrice: parseInt(getFromQuery('maxPrice')) || null,
    sortBy: ensureAllowedName(getFromQuery('sortBy', 'name'), SORT_BY_FIELDS)
  },
  fragments: {
    category: () => Relay.QL`
      fragment on CategoryType {
        pk
        name
        url
        ancestors {
          name
          pk
          url
        }
        children {
          name
          pk
          url
          slug
        }
        products (
          first: $count,
          attributes: $attributesFilter,
          priceGte: $minPrice,
          priceLte: $maxPrice,
          orderBy: $sortBy
        ) {
          ${ProductList.getFragment('products')}
        }
      }
    `
  }
});
