import React, { Component } from 'react';
import ReactSVG from 'react-svg';
import axios from 'axios';

import css from './githublink.css';

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
      <a className="githubLink" href={`https://github.com/${this.props.owner}/${this.props.name}`}>
        <ReactSVG className="github-icon" svgStyle={{ width: 25, height: 25 }} path="images/github-icon.svg" />
        <ReactSVG className="star-icon" svgStyle={{ width: 15, height: 15 }} path="images/star-icon.svg" />
        <span className="star-value">{this.state.stars}</span>
      </a>
    );
  }
}

export default GitHubLink;
