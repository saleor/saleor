import 'jquery.cookie';
import React from 'react';
import { render } from 'react-dom';
import { createStore } from 'redux';
import { Provider } from 'react-redux';
import { ApolloClient } from 'apollo-client';
import { HttpLink } from 'apollo-link-http';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { ApolloProvider } from 'react-apollo';
import { BrowserRouter, Route, Switch } from 'react-router-dom';

import CategorySection from './category';

const apolloClient = new ApolloClient({
  link: new HttpLink({
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': $.cookie('csrftoken')
    }
  }),
  cache: new InMemoryCache(),
});
const routerMapping = [
  {
    component: CategorySection,
    path: 'categories',
    param: 'pk'
  }
];
const store = createStore(() => {});

render(
  <Provider store={store}>
    <ApolloProvider client={apolloClient}>
      <BrowserRouter>
        <Switch>
          {routerMapping.map(route => (
            <div>
              <Route path={(() => `/dashboard/${route.path}/`)()}
                     component={route.component}
                     exact />
              {route.param && (
                <Route path={(() => `/dashboard/${route.path}/${route.param ? (':' + route.param) : ''}`)()}
                       component={route.component}
                       exact />
              )}
            </div>
          ))}
        </Switch>
      </BrowserRouter>
    </ApolloProvider>
  </Provider>,
  document.querySelector('#dashboard-app')
);
