import { ApolloClient } from 'apollo-client';
import { createHttpLink } from 'apollo-link-http';
import { InMemoryCache } from 'apollo-cache-inmemory';

const link = createHttpLink({
  uri: '/graphql',
  credentials: 'same-origin',
  headers: {
    'X-CSRFToken': $.cookie('csrftoken')
  }
});

const client = new ApolloClient({
  cache: new InMemoryCache(),
  link,
  connectToDevTools: true
});

export default client;
