import React, { PropTypes } from 'react';
import ReactDOM from 'react-dom';
import Relay from 'react-relay';

import ReleasesPage from './components/releasePage/ReleasesPage';
import Loading from './components/Loading';
import {getReleaseListColumnNumber} from "./components/utils";

const releasesPage = document.getElementById('releases-page');

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
      if (!this.state.loading
              && (window.innerHeight + window.scrollY)
              >= releasesPage.offsetHeight/3) {

        this.setState({loading: true}, () => {
          this.props.relay.setVariables({
            count: this.props.relay.variables.count + PAGINATE_BY * getReleaseListColumnNumber()
          }, (readyState) => {
            if (readyState.done) {
              this.setState({ loading: false });
            }
          });
        });
      }
    }
  }

  render() {
    return <ReleasesPage {...this.props.root} />;
  }
}

const RelayApp = Relay.createContainer(App, {
  initialVariables: {
    count: PAGINATE_BY * getReleaseListColumnNumber()
  },
  fragments: {
    root: () => Relay.QL`
      fragment on Query {
        releases (first: $count) {
          ${ReleasesPage.getFragment('releases')}
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
  params: {
  },
  name: 'Root'
};

ReactDOM.render(
  <Relay.RootContainer
   Component={RelayApp}
   route={AppRoute}
   renderLoading={() => <Loading />}
  />,
  releasesPage
);
