import React, { Component, createContext } from "react";

import { GH_OWNER, GH_REPO } from "../consts";

const GitHubStarsContext = createContext(null);

class GitHubStarsProvider extends Component {
  constructor(props) {
    super(props);
    this.state = {
      stars: null
    };
  }

  async updateStars() {
    const clientID = "Iv1.f57e790baceb1324&";
    const clientSecret = "6fa1790eddb3149031446293e62f92da52c50f9e";

    const apiUrl = `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}?client_id=${clientID}client_secret=${clientSecret}`;

    const response = await fetch(apiUrl);
    const data = await response.json();

    this.setState({
      stars: data.watchers_count
    });
  }

  async componentDidMount() {
    await this.updateStars();
  }

  render() {
    return (
      <GitHubStarsContext.Provider value={this.state.stars}>
        {this.props.children}
      </GitHubStarsContext.Provider>
    );
  }
}

const { Consumer } = GitHubStarsContext;

export { GitHubStarsProvider };
export default Consumer;
