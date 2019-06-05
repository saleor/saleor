import React from "react";
import ReactSVG from "react-svg";

import { GH_OWNER, GH_REPO } from "../../consts";
import GitHubStars from "../GitHubStars";

import css from "./githublink.css";

const GitHubLink = ({ text }) => (
  <GitHubStars>
    {stars => (
      <a
        className="githubLink"
        href={`https://github.com/${GH_OWNER}/${GH_REPO}`}
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
        <span className="star-value">{stars} </span>
        {text && <p className="github-text">{text}</p>}
      </a>
    )}
  </GitHubStars>
);

export default GitHubLink;
