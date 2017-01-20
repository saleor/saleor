import React from 'react';

import noResultsImg from '../../../img/pirate.svg';

const NoResults = () => {
  return (
    <div>
      <img src={noResultsImg} />
      <p>Sorry, no matches found for your request. Try again or shop new arrivals</p>
    </div>
  );
};

export default NoResults;
