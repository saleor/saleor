import React, {PropTypes} from 'react';
import {gql, graphql} from 'react-apollo';

import Loading from '../Loading';
import CategoryPage from './CategoryPage';
import ProductFilters from "./ProductFilters";


class App extends React.Component {
  static propTypes = {
    root: PropTypes.object
  };

  constructor(props) {
    super(props);
  }

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
    $categoryId: Int!,
    $sortBy: String,
    $first: Int,
    $attributesFilter: [AttributesFilterScalar],
    $minPrice: Float,
    $maxPrice: Float
  ) {
    category(pk: $categoryId) {
      ...CategoryPageFragmentQuery

    }
    attributes(categoryPk: $categoryId) {
      ...ProductFiltersFragmentQuery
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
