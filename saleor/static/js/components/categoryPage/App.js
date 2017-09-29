import React, {PropTypes} from 'react';
import ReactDOM from 'react-dom';
import {ApolloProvider, ApolloClient, gql, graphql} from 'react-apollo';

import Loading from '../Loading';
import CategoryPage from './CategoryPage';
import ProductFilters from "./ProductFilters";


class App extends React.Component {
  static propTypes = {
    root: PropTypes.object
  };

  constructor(props) {
    super(props);
    if (!this.props.categoryId) {
      this.props.categoryId = 1;
    }
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
  options: ({categoryId, sortBy, first, attributesFilter, minPrice, maxPrice}) => ({
    variables: {
      categoryId,
      sortBy: '',
      first: 24,
      attributesFilter: [],
      minPrice: null,
      maxPrice: null
    }
  })
})(App);
