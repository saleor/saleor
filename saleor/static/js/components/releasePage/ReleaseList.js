import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import ReleaseItem from './ReleaseItem';
import NoResults from './NoResults';

class ReleaseList extends Component {

  static propTypes = {
    releases: PropTypes.object,
  };

  render() {
    const { edges, pageInfo: { hasNextPage } } = this.props.releases;
    return (
      <div>
        <div className="row">
          {edges.length > 0 ? (edges.map((edge, i) => (
            <ReleaseItem key={i} release={edge.node} />
          ))) : (<NoResults />)}
        </div>
      </div>
    );
  }
}

export default Relay.createContainer(ReleaseList, {
  fragments: {
    releases: () => Relay.QL`
      fragment on ArtikelTypeConnection {
        edges {
          node {
            ${ReleaseItem.getFragment('product')}
          }
        }
        pageInfo {
          hasNextPage
        }
      }
    `
  }
});
