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
  query Root($categoryId: Int!, $sortBy: String, $first: Int) {
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
  options: ({categoryId, sortBy, first}) => ({
    variables: {
      categoryId,
      sortBy: '',
      first: 24
    }
  })
})(App);
