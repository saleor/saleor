import React from "react";

import css from "./scrolllink.css";
import arrowDownIcon from "../../images/arrow-down-icon.png";

const ScrollButton = props => (
  <div className="scroll-link">
    <a href={props.to}>
      <span>{props.children}</span>
      <img src={arrowDownIcon} alt="Learn more" />
    </a>
  </div>
);

export default ScrollButton;
