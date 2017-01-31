import * as React from 'react';
import * as ReactDOM from 'react-dom';
import * as Relay from 'react-relay';

import CategoryPage from './components/categoryPage/CategoryPage';
import ProductFilters from './components/categoryPage/ProductFilters';
import Loading from './components/Loading';

const categoryPage = document.getElementById('category-page');
const categoryData = JSON.parse(categoryPage.getAttribute('data-category'));

interface AppProps {
  root: {};
};

class App extends React.Component<AppProps, {}> {
  render() {
    return <CategoryPage {...this.props.root} />;
  }
}

const RelayApp = Relay.createContainer(App, {
  initialVariables: {
    categoryId: categoryData.id
  },
  fragments: {
    root: () => Relay.QL`
      fragment on Query {
        category(pk: $categoryId) {
          ${CategoryPage.getFragment('category')}
        }
        attributes(categoryPk: $categoryId) {
          ${ProductFilters.getFragment('attributes')}
        }
        __debug {
          sql {
            sql
          }
        }
      }
    `
  }
});

const AppRoute = {
  queries: {
    root: () => Relay.QL`
      query { root }
    `
  },
  params: {},
  name: 'Root'
};

ReactDOM.render(
  <Relay.RootContainer
   Component={RelayApp}
   route={AppRoute}
   renderLoading={() => <Loading />}
  />,
  categoryPage
);
