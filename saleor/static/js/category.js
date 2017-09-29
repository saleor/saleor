import queryString from 'query-string';
import React, {PropTypes} from 'react';
import ReactDOM from 'react-dom';
import Relay from 'react-relay/classic';
import {ApolloProvider, ApolloClient, gql, graphql, createNetworkInterface} from 'react-apollo';
import 'jquery.cookie';

import ProductFilters from './components/categoryPage/ProductFilters';
import App from './components/categoryPage/App';

import {ensureAllowedName, getAttributesFromQuery, getFromQuery} from './Components/CategoryPage/utils';

const categoryPage = document.getElementById('category-page');
const categoryData = JSON.parse(categoryPage.getAttribute('data-category'));
const SORT_BY_FIELDS = ['name', 'price'];

const networkInterface = createNetworkInterface({
  uri: '/graphql',
  opts: {
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': $.cookie('csrftoken')
    }
  }
});
const apolloClient = new ApolloClient({networkInterface});

// const RelayApp = Relay.createContainer(App, {
//   initialVariables: {
//     categoryId: categoryData.id
//   },
//   fragments: {
//     root: () => Relay.QL`
//       fragment on Query {
//         category(pk: $categoryId) {
//           ${CategoryPage.getFragment('category')}
//         }
//         attributes(categoryPk: $categoryId) {
//           ${ProductFilters.getFragment('attributes')}
//         }
//       }
//     `
//   }
// });

// const AppRoute = {
//   queries: {
//     root: () => Relay.QL`
//       query { root }
//     `
//   },
//   params: {},
//   name: 'Root'
// };
//
// ReactDOM.render(
//     <Relay.RootContainer
//       Component={RelayApp}
//       route={AppRoute}
//       renderLoading={() => <Loading/>}
//     />,
//     categoryPage
// );

ReactDOM.render(
  <ApolloProvider client={apolloClient}>
    <App
      categoryId={categoryData.id}
      minPrice={parseInt(getFromQuery('minPrice')) || null}
      maxPrice={parseInt(getFromQuery('maxPrice')) || null}
      attributesFilter={getAttributesFromQuery(['count', 'minPrice', 'maxPrice', 'sortBy']) || []}
      sortBy={ensureAllowedName(getFromQuery('sortBy', 'name'), SORT_BY_FIELDS)}
    />
  </ApolloProvider>,
  categoryPage
);
