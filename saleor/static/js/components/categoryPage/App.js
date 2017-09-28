import React, {PropTypes} from 'react';
import ReactDOM from 'react-dom';
import {ApolloProvider, ApolloClient, gql, graphql} from 'react-apollo';

import Loading from '../Loading';
import CategoryPage from './CategoryPage';


class App extends React.Component {
  static propTypes = {
    root: PropTypes.object
  };

  constructor(props) {
    super(props);
    if (!this.props.categoryId) {
      this.props.categoryId = 1;
    }
    this.props.sortBy = '';
  }

  render() {
    if (this.props.data.loading) {
      return <Loading/>;
    } else {
      return <CategoryPage {...this.props} />;
    }
  }
}

const rootQuery = gql`
  query Root($categoryId: Int!, $sortBy: String) {
    category(pk: $categoryId) {
      ...CategoryPageFragmentQuery

    }
    attributes(categoryPk: $categoryId) {
      id
    }
  }
  ${CategoryPage.fragments.category}
`;

export default graphql(rootQuery, {
  options: ({categoryId, sortBy}) => ({
    variables: {categoryId, sortBy}
  })
})(App);
