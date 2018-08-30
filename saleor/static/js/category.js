import React from 'react';
import { ApolloClient } from 'apollo-client';
import { createHttpLink } from 'apollo-link-http';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { ApolloProvider } from 'react-apollo';
import { render } from 'react-dom';

import App from './components/categoryPage/App';

import { ensureAllowedName, getAttributesFromQuery, getFromQuery } from './components/categoryPage/utils';

const categoryPage = document.getElementById('category-page');
const categoryData = JSON.parse(categoryPage.getAttribute('data-category'));
const SORT_BY_FIELDS = ['name', 'price'];
const PAGINATE_BY = 24;

const client = new ApolloClient({
  link: createHttpLink({ uri: '/graphql/' }),
  cache: new InMemoryCache()
});

const WrappedApp = (
  <ApolloProvider client={client}>
    <App
      categoryId={categoryData.id}
      minPrice={parseInt(getFromQuery('minPrice')) || null}
      maxPrice={parseInt(getFromQuery('maxPrice')) || null}
      attributesFilter={getAttributesFromQuery(['count', 'minPrice', 'maxPrice', 'sortBy']) || []}
      sortBy={ensureAllowedName(getFromQuery('sortBy', 'name'), SORT_BY_FIELDS)}
      PAGINATE_BY={PAGINATE_BY}
    />
  </ApolloProvider>
);

render(WrappedApp, categoryPage);
