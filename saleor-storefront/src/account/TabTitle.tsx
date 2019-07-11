import "./scss/tabTitle.scss";

import React from "react";
import { Link } from "react-router-dom";

export interface ITabTitle {
  element: string;
  active: string;
}

const TabTitle: React.FC<ITabTitle> = ({ element, active }) => (
  <div className="tab-title">
    <Link to={element} className="tab-title__link">
      {element.replace("-", " ").toUpperCase()}
    </Link>
    {active === element ? <div className="tab-title__link__underline" /> : ""}
  </div>
);

export default TabTitle;
