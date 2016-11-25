import React from 'react'
import ReactDOM from 'react-dom'
import Relay from 'react-relay';

import CategoryPage from './components/CategoryPage'


Relay.injectNetworkLayer(
    new Relay.DefaultNetworkLayer('/graphql/', {
        credentials: 'same-origin',
    })
);

class App extends React.Component {
  render() {
    return <CategoryPage products={ this.props.viewer.products.edges } />
  }
}

const RelayApp = Relay.createContainer(App, {
  fragments: {
    viewer: () => Relay.QL`
      fragment on Viewer {
        products(first: 20) {
          edges {
            node {
              id,
              name,
              description,
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
  document.getElementById('category-page'),
);
