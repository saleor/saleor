import React from 'react';
import * as PropTypes from 'prop-types';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';

import Loading from '../Loading';
import CategoryPage from './CategoryPage';
import ProductFilters from './ProductFilters';

class App extends React.Component {
  static propTypes = {
    root: PropTypes.object
  };

  render() {
    if (this.props.data.loading && !this.props.data.category) {
      return <Loading/>;
    } else {
      return <div><CategoryPage {...this.props} /></div>;
    }
  }
}

const rootQuery = gql`
  query Root(
    $categoryId: ID!,
    $sortBy: String,
    $first: Int,
    $attributesFilter: [AttributeScalar],
    $minPrice: Float,
    $maxPrice: Float
  ) {
    category(id: $categoryId) {
      ...CategoryPageFragmentQuery
    }
    attributes(inCategory: $categoryId) {
      edges {
        node {
          ...ProductFiltersFragmentQuery
        }
      }
    }
  }
  ${CategoryPage.fragments.category}
  ${ProductFilters.fragments.attributes}
`;

export default graphql(rootQuery, {
  options: ({categoryId, sortBy, PAGINATE_BY, attributesFilter, minPrice, maxPrice}) => ({
    variables: {
      categoryId,
      sortBy: sortBy,
      first: PAGINATE_BY,
      attributesFilter: attributesFilter,
      minPrice: minPrice,
      maxPrice: maxPrice
    },
    fetchPolicy: 'cache-and-network'
  })
})(App);
