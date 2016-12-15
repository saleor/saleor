import queryString from 'query-string';
import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import CategoryFilter from './CategoryFilter';
import PriceFilter from './PriceFilter';
import ProductFilters from './ProductFilters';
import ProductList from './ProductList';


const PAGINATE_BY = 20;


const getVarFromQueryString = (key, defaultValue = null) => {
  let value = queryString.parse(location.search)[key];
  return value ? value : defaultValue;
};


const floatOrNull = (value) => {
  const parsed = parseFloat(value);
  return isNaN(parsed) ? null : parsed;
};


class CategoryPage extends Component {

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

  updateAttributesFilter = (attributes) => {
    this.props.relay.setVariables({attributesFilter: attributes});
  }

  updatePriceFilter = (minPrice, maxPrice) => {
    this.props.relay.setVariables({
      minPrice: floatOrNull(minPrice),
      maxPrice: floatOrNull(maxPrice)
    });
  }

  persistStateInUrl() {
    const { attributesFilter, count, maxPrice, minPrice } = this.props.relay.variables;
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
    attributesFilter.forEach(filter => {
      const [ attributeName, valueSlug ] = filter.split(':');
      if (attributeName in urlParams) {
        urlParams[attributeName].push(valueSlug);
      } else {
        urlParams[attributeName] = [valueSlug];
      }
    });
    const url = Object.keys(urlParams).length ?
      '?' + queryString.stringify(urlParams) :
      location.href.split('?')[0];
    history.pushState({}, null , url);
  }

  componentDidUpdate() {
    // Persist current state of relay variables as query string. Current
    // variables are available in props after component rerenders, so it has to
    // be called inside componentDidUpdate method.
    this.persistStateInUrl();
  }

  render() {
    const { attributes, category, relay: { variables } } = this.props;
    return (
      <div className="row">
        <div className="col-md-3">
          <h2>Filters:</h2>
          <div className="product-filters">
            <CategoryFilter
              category={category}
            />
            <ProductFilters
              attributes={attributes}
              onFilterChanged={this.updateAttributesFilter}
            />
            <PriceFilter
              onFilterChanged={this.updatePriceFilter}
              maxPrice={variables.maxPrice}
              minPrice={variables.minPrice}
            />
          </div>
        </div>
        <div className="col-md-9">
          <div className="row">
            <ProductList
              onLoadMore={this.incrementProductsCount}
              products={category.products}
            />
          </div>
        </div>
      </div>
    );
  }
}


export default Relay.createContainer(CategoryPage, {
  initialVariables: {
    attributesFilter: [],
    count: floatOrNull(getVarFromQueryString('count', PAGINATE_BY)),
    minPrice: floatOrNull(getVarFromQueryString('minPrice')),
    maxPrice: floatOrNull(getVarFromQueryString('maxPrice'))
  },
  fragments: {
    category: () => Relay.QL`
      fragment on CategoryType {
        pk
        name
        url
        productsCount
        siblings {
          name
          pk
          url
          productsCount
        }
        products (first: $count, attributes: $attributesFilter, priceGte: $minPrice, priceLte: $maxPrice) {
          ${ProductList.getFragment('products')}
        }
      }
    `,
  },
});
