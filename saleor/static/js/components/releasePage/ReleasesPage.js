import queryString from 'query-string';
import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import ReleaseItem from './ReleaseItem';

import { ensureAllowedName, getAttributesFromQuery, getFromQuery } from '../categoryPage/utils';
import {isMobile} from '../utils';

export const PAGINATE_BY = 20;
const SORT_BY_FIELDS = ['name', 'price'];

class ReleasesPage extends Component {

  constructor(props) {
    super(props);
    this.state = {
      filtersMenu: !isMobile()
    };
  }

  static propTypes = {
    attributes: PropTypes.array,
    releases: PropTypes.object,
    relay: PropTypes.object
  }

  persistStateInUrl() {
    const { attributesFilter, count } = this.props.relay.variables;
    let urlParams = {};
    attributesFilter.forEach(filter => {
      const [ attributeName, valueSlug ] = filter.split(':');
      if (attributeName in urlParams) {
        urlParams[attributeName].push(valueSlug);
      } else {
        urlParams[attributeName] = [valueSlug];
      }
    });
    const url = Object.keys(urlParams).length ? '?' + queryString.stringify(urlParams) : location.href.split('?')[0];
    history.pushState({}, null, url);
  }

  componentDidUpdate() {
    // Persist current state of relay variables as query string. Current
    // variables are available in props after component rerenders, so it has to
    // be called inside componentDidUpdate method.
    this.persistStateInUrl();
  }

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

export default Relay.createContainer(ReleasesPage, {
  initialVariables: {
    attributesFilter: getAttributesFromQuery(['count', 'minPrice', 'maxPrice', 'sortBy']),
    count: parseInt(getFromQuery('count', PAGINATE_BY)) || PAGINATE_BY,
    minPrice: parseInt(getFromQuery('minPrice')) || null,
    maxPrice: parseInt(getFromQuery('maxPrice')) || null,
    sortBy: ensureAllowedName(getFromQuery('sortBy', 'name'), SORT_BY_FIELDS)
  },
  fragments: {
    releases: () => Relay.QL`
      fragment on ArtikelTypeConnection {
        edges {
          node {
            ${ReleaseItem.getFragment('release')}
          }
        }
        pageInfo {
          hasNextPage
        }
      }
    `
  }
});
