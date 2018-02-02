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
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import { createMuiTheme } from 'material-ui/styles';


import CategorySection from './category/index';

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
const theme = createMuiTheme({
  palette: {
    primary: {
      main: '#2bb673',
    },
    secondary: {
      main: '#26A5D4',
    },
  }
});

render(
  <Provider store={store}>
    <ApolloProvider client={apolloClient}>
      <BrowserRouter basename={'/dashboard'}>
        <MuiThemeProvider theme={theme}>
          <Switch>
            {routerMapping.map(route => (
              <div>
                <Route path={(() => `/${route.path}/`)()}
                       component={route.component}
                       exact />
                {route.param && (
                  <Route path={(() => `/${route.path}/${route.param ? (':' + route.param) : ''}`)()}
                         component={route.component}
                         exact />
                )}
              </div>
            ))}
          </Switch>
        </MuiThemeProvider>
      </BrowserRouter>
    </ApolloProvider>
  </Provider>,
  document.querySelector('#dashboard-app')
);
