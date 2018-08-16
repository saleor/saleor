import React from 'react';

import css from './githubbanner.css';

const GitHubBanner = (props) => (
	<section className="github-banner text-center">
    <h1>simple <span className="text-light">is</span> better</h1>
    <h1>less <span className="text-light">is</span> more</h1>
    <h1>saleor <span className="text-light">is</span> free</h1>
    <a className="btn btn-primary" href="https://github.com/mirumee/saleor" target="_blank">Fork it on Github</a>
    <div className="decoration decoration-left">
      <img src="../../images/decoration07.png" />
    </div>
    <div className="decoration decoration-right">
      <img src="../../images/decoration09.png" />
    </div>
  </section>
);

export default GitHubBanner;