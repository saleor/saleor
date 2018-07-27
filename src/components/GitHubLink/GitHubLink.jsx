import React, { Component } from 'react';
import ReactSVG from 'react-svg';
import axios from 'axios';


class GitHubLink extends Component {

  constructor(props) {
    super(props);
    this.state = {stars: null};
  }

  updateStars() {
    const apiUrl = `https://api.github.com/repos/${this.props.owner}/${this.props.name}`;
    const stars = axios.get(apiUrl);
    stars.then((response) => {
      if (response.status === 200) {
        this.setState({stars: response.data.watchers_count});
      }
    });
  }

  componentDidMount() {
    this.updateStars()
  }

  render() {
    return (
      <a href={`https://github.com/${this.props.owner}/${this.props.name}`}>
        <ReactSVG path="images/github.svg" />
        <ReactSVG path="images/star.svg" />
        {this.state.stars}
      </a>
    );
  }
}

export default GitHubLink;
