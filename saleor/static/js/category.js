import React from 'react';
import ReactDOM from 'react-dom';
import {ApolloProvider, ApolloClient, createNetworkInterface} from 'react-apollo';
import 'jquery.cookie';

import App from './components/categoryPage/App';

import {ensureAllowedName, getAttributesFromQuery, getFromQuery} from './components/categoryPage/utils';

const categoryPage = document.getElementById('category-page');
const categoryData = JSON.parse(categoryPage.getAttribute('data-category'));
const SORT_BY_FIELDS = ['name', 'price'];
const PAGINATE_BY = 24;

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

ReactDOM.render(
  <ApolloProvider client={apolloClient}>
    <App
      categoryId={categoryData.id}
      minPrice={parseInt(getFromQuery('minPrice')) || null}
      maxPrice={parseInt(getFromQuery('maxPrice')) || null}
      attributesFilter={getAttributesFromQuery(['count', 'minPrice', 'maxPrice', 'sortBy']) || []}
      sortBy={ensureAllowedName(getFromQuery('sortBy', 'name'), SORT_BY_FIELDS)}
      PAGINATE_BY={PAGINATE_BY}
    />
  </ApolloProvider>,
  categoryPage
);
