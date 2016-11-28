import React from 'react'
import ReactDOM from 'react-dom'
import Relay from 'react-relay';

import CategoryPage from './components/CategoryPage'

const categoryPage = document.getElementById('category-page');
const categoryData = JSON.parse(categoryPage.getAttribute('data-category'));


Relay.injectNetworkLayer(
    new Relay.DefaultNetworkLayer('/graphql/', {
        credentials: 'same-origin',
    })
);

class App extends React.Component {
  render() {
    return (
        <CategoryPage 
          products={ this.props.viewer.category.products.edges }
          categoryName = { this.props.viewer.category.name }
          categories= { this.props.viewer.category.children.edges }
        />
      );
  }
}

const RelayApp = Relay.createContainer(App, {
  initialVariables: {
    categoryId: categoryData.id
  },
  fragments: {
    viewer: () => Relay.QL`
      fragment on Viewer {
        category(pk: $categoryId) {
          id,
          name,
          children(first: 20) {
            edges {
              node {
                id,
                name,
                slug
              }
            }
          },
          products(first: 20) {
            edges {
              node {
                id,
                name,
                imageUrl,
                price {
                  gross,
                  currency
                },
                url
              }
            }
          }
        }
      }
    `,
  },
});

const Viewer = {
  queries: {
    viewer: () => Relay.QL`
      query { viewer }
    `,
  },
  params: {},
  name: 'Viewer',
};

ReactDOM.render(
  <Relay.RootContainer
    Component={RelayApp}
    route={Viewer}
    />,
  categoryPage,
);
