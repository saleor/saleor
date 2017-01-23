import React from 'react';

import noResultsImg from '../../../img/pirate.svg';

const NoResults = () => {
  return (
    <div className="no-results">
        <div className="col-12">
            <img src={noResultsImg} />
            <p>Sorry, no matches found for your request.</p>
            <p>Try again or shop new arrivals.</p>
        </div>
    </div>
  );
};

export default NoResults;
