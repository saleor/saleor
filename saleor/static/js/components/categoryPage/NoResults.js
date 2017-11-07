import React from 'react';
import InlineSVG from 'react-inlinesvg';

import noResultsImg from '../../../images/pirate.svg';

const NoResults = () => {
  return (
    <div className="no-results">
      <div className="col-12">
        <InlineSVG src={noResultsImg} />
        <p>{pgettext('Epty search results', 'Sorry, no matches found for your request.')}</p>
        <p>{pgettext('Epty search results', 'Try again or shop new arrivals.')}</p>
      </div>
    </div>
  );
};

export default NoResults;
