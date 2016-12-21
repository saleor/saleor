import queryString from 'query-string';
import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import CategoryFilter from './CategoryFilter';
import PriceFilter from './PriceFilter';
import ProductFilters from './ProductFilters';
import ProductList from './ProductList';
import SortBy from './SortBy';


const PAGINATE_BY = 20;


const getVarFromQueryString = (key, defaultValue = null) => {
  let value = queryString.parse(location.search)[key];
  return value ? value : defaultValue;
};


const getAttributesFromQueryString = (exclude) => {
  // Exclude parameter is used to exclude other query string parameters than
  // product attribute filters.
  const urlParams = queryString.parse(location.search);
  let attributes = [];
  Object.keys(urlParams).forEach(key => {
    if (!exclude.includes(key)) {
      if (Array.isArray(urlParams[key])) {
        const values = urlParams[key];
        values.map((valueSlug) => {
          attributes.push(`${key}:${valueSlug}`);
        });
      } else {
        const valueSlug = urlParams[key];
        attributes.push(`${key}:${valueSlug}`);
      }
    }
  });
  return attributes;
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

  setSorting = (event) => {
    this.props.relay.setVariables({
      sortBy: event.target.className
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
      minPrice: floatOrNull(minPrice),
      maxPrice: floatOrNull(maxPrice)
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
      <div className="category-page">
        <div className="category-top">
          <div className="row">
            <div className="col-md-8">
              <ul className="category-breadcrumbs">
                <li><a href="/">Home</a></li>
                  {category.ancestors && (category.ancestors.map((ancestor) => {
                    return (
                      <li key={ancestor.pk}><a href={ancestor.url}>{ancestor.name}</a></li>
                    );
                  }))}
                <li><a href={category.url}>{category.name}</a></li>
              </ul>
            </div>
            <div className="col-md-4">
              <SortBy sortedValue={variables.sortBy} setSorting={this.setSorting} />
            </div>
          </div>
        </div>
        <div className="row">
          <div className="col-md-3">
            <div className="product-filters">
              <CategoryFilter
                category={category}
              />
            </div>
            <h2>Filters:</h2>
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
          <div className="col-md-9">
            <div className="row">
              <ProductList
                onLoadMore={this.incrementProductsCount}
                products={category.products}
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
    attributesFilter: getAttributesFromQueryString(['count', 'minPrice', 'maxPrice', 'sortBy']),
    count: floatOrNull(getVarFromQueryString('count', PAGINATE_BY)),
    minPrice: floatOrNull(getVarFromQueryString('minPrice')),
    maxPrice: floatOrNull(getVarFromQueryString('maxPrice')),
    sortBy: getVarFromQueryString('sortBy')
  },
  fragments: {
    category: () => Relay.QL`
      fragment on CategoryType {
        pk
        name
        url
        parent {
          id
          name,
          url
        }
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
          children {
            name
            pk
            url
            slug
          }
        }
        products (first: $count, attributes: $attributesFilter, priceGte: $minPrice, priceLte: $maxPrice, orderBy: $sortBy) {
          ${ProductList.getFragment('products')}
        }
      }
    `,
  },
});
