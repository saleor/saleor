import React, {PropTypes} from "react";
import ReactDOM from "react-dom";
import Relay from "react-relay";
import {Router, Route, browserHistory} from "react-router";
import applyRouterMiddleware from "react-router/lib/applyRouterMiddleware";
import useRelay from "react-router-relay";
import ReleasesPage from "./components/releasePage/ReleasesPage";
import ReleaseDetailView from "./components/releasePage/ReleaseDetailView";
import Loading from "./components/Loading";
import {getReleaseListColumnNumber} from "./components/utils";

// url routing/history stuff

const releasesPage = document.getElementById('releases-page');
const releaseData = JSON.parse(releasesPage.getAttribute('data-releases'));

const PAGINATE_BY = 10;

class App extends React.Component {

  constructor(props) {
    super(props)
    this.state = {
      loading: false
    };
  }

  static propTypes = {
    root: PropTypes.object,
  }

  componentDidMount() {
    window.onscroll = () => {
      if (!this.props.relay.variables.showDetailPage
        && !this.state.loading
        && (window.innerHeight + window.scrollY)
        >= releasesPage.offsetHeight / 3) {

        this.setState({loading: true}, () => {
          this.props.relay.setVariables({
            count: this.props.relay.variables.count + PAGINATE_BY * getReleaseListColumnNumber()
          }, (readyState) => {
            if (readyState.done) {
              this.setState({loading: false});
            }
          });
        });
      }
    }
  }

  onShowList = () => {
    this.props.relay.setVariables({
      showDetailPage: false
    })
  }

  onNavigate = (id, updateHistory = true) => {
    this.props.relay.setVariables({
      releaseId: id,
      showDetailPage: true
    })
  }

  render() {
    var isRefreshing = this.state.loading;
    return this.props.relay.variables.showDetailPage ?
      <ReleaseDetailView release={this.props.root.release} onShowList={this.onShowList} /> :
      <div>
        <ReleasesPage {...this.props.root} onNavigate={this.onNavigate}/>
        <Loading style={{display: isRefreshing ? 'block' : 'none'}}/>
      </div>
  }
}

const RelayApp = Relay.createContainer(App, {
  initialVariables: {
    count: PAGINATE_BY * getReleaseListColumnNumber(),
    filterBy: JSON.stringify(releaseData.filterBy),
    showDetailPage: false,
    releaseId: window.location.pathname.substr(1)
  },
  fragments: {
    root: () => Relay.QL`
      fragment on Query {
        releases (first: $count, filterBy: $filterBy) @skip(if: $showDetailPage) {
          ${ReleasesPage.getFragment('releases')}
        }
        release(pk: $releaseId) @include(if: $showDetailPage) {
          ${ReleaseDetailView.getFragment('release')}
        }
       }
    `
  },

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
  <Router history={browserHistory}
          render={applyRouterMiddleware(useRelay)}
          environment={Relay.Store}>
    <Route name="releases"
           path="/oye/releases/*"
           component={RelayApp}
           queries={AppRoute.queries}/>
  </Router>,
  releasesPage
);
