import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import CategoryFilter from './CategoryFilter';
import PriceFilter from './PriceFilter';
import ProductFilters from './ProductFilters';
import ProductList from './ProductList';

const PAGINATE_BY = 20;


class CategoryPage extends Component {

  static propTypes = {
    attributes: PropTypes.array,
    category: PropTypes.object,
    relay: PropTypes.object
  }

  loadMore = () => {
    this.props.relay.setVariables({
      count: this.props.relay.variables.count + PAGINATE_BY
    })
  }

  setAttributesFilter = (attributes) => {
    this.props.relay.setVariables({
      attributesFilter: attributes
    });
  }

  setPriceFilter = (minPrice, maxPrice) => {
    this.props.relay.setVariables({
      minPrice: minPrice,
      maxPrice: maxPrice
    });
  }

  render() {
    const category = this.props.category;
    const attributes = this.props.attributes;
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
              onFilterChanged={this.setAttributesFilter}
            />
            <PriceFilter
              onFilterChanged={this.setPriceFilter}
            />
          </div>
        </div>
        <div className="col-md-9">
          <div className="row">
            <ProductList
              onLoadMore={this.loadMore}
              products={category.products}
            />
          </div>
        </div>    
      </div>
    )
  }
}

export default Relay.createContainer(CategoryPage, {
  initialVariables: {
    attributesFilter: [],
    count: PAGINATE_BY,
    minPrice: null,
    maxPrice: null
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
