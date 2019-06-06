import React from "react";

import css from "./githubbanner.css";

const GitHubBanner = props => (
  <section className="github-banner text-center">
    <h1>
      simple <span className="text-light">is</span> better
    </h1>
    <h1>
      less <span className="text-light">is</span> more
    </h1>
    <h1>
      saleor <span className="text-light">is</span> free
    </h1>
    <a
      className="btn btn-secondary"
      href="https://github.com/mirumee/saleor"
      target="_blank"
      rel="noopener"
    >
      <span>Fork it on Github</span>
    </a>
  </section>
);

export default GitHubBanner;
