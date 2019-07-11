import * as React from "react";

import "./scss/index.scss";

const Loader: React.FC<{ full?: boolean }> = ({ full }) => {
  const getHeight = () => {
    const headerHeight =
      document.getElementById("header") &&
      document.getElementById("header").offsetHeight;
    const footerHeight =
      document.getElementById("footer") &&
      document.getElementById("footer").offsetHeight;
    return window.innerHeight - headerHeight - footerHeight;
  };

  return (
    <div className="loader" style={full && { height: getHeight() }}>
      <div className="loader__items">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
};

export default Loader;
