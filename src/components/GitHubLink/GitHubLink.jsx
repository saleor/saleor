import React, { Component } from "react";
import ReactSVG from "react-svg";
import axios from "axios";

import css from "./githublink.css";

class GitHubLink extends Component {
  constructor(props) {
    super(props);
    this.state = {
      stars: null
    };
  }

  updateStars() {
    const clientID = "Iv1.f57e790baceb1324&";
    const clientSecret = "6fa1790eddb3149031446293e62f92da52c50f9e";
    const apiUrl = `https://api.github.com/repos/${this.props.owner}/${
      this.props.name
    }?client_id=${clientID}client_secret=${clientSecret}`;
    const request = new XMLHttpRequest();
    request.open("GET", apiUrl);
    request.send();
    request.onreadystatechange = () => {
      const DONE = 4;
      const OK = 200;
      if (request.readyState === DONE && request.status === OK) {
        const response = JSON.parse(request.responseText);
        this.setState({ stars: response.watchers_count });
      }
    };
  }

  componentDidMount() {
    this.updateStars();
  }

  render() {
    const text = this.props.text;
    return (
      <a
        className="githubLink"
        href={`https://github.com/${this.props.owner}/${this.props.name}`}
      >
        <ReactSVG
          className="github-icon"
          svgStyle={{ width: 25, height: 25 }}
          path="images/github-icon.svg"
        />
        <ReactSVG
          className="star-icon"
          svgStyle={{ width: 15, height: 15 }}
          path="images/star-icon.svg"
        />
        <span className="star-value">{this.state.stars} </span>
        {text && <p className="github-text">{text}</p>}
      </a>
    );
  }
}

export default GitHubLink;
