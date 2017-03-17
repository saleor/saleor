import React, { PropTypes } from 'react';
import ReactDOM from 'react-dom';
import Relay from 'react-relay';

import CategoryPage from './components/categoryPage/CategoryPage';
import ProductFilters from './components/categoryPage/ProductFilters';
import Loading from './components/Loading';

const categoryPage = document.getElementById('category-page');
const categoryData = JSON.parse(categoryPage.getAttribute('data-category'));

class App extends React.Component {

  static propTypes = {
    root: PropTypes.object
  }

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
