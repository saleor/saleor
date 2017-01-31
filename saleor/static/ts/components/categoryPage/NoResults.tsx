import * as React from 'react';
import InlineSVG from 'react-inlinesvg';

let noResultsImg = require('../../../images/pirate.svg');

const NoResults = () => {
  return (
    <div className="no-results">
      <div className="col-12">
        <InlineSVG src={noResultsImg} />
        <p>{gettext('Sorry, no matches found for your request.')}</p>
        <p>{gettext('Try again or shop new arrivals.')}</p>
      </div>
    </div>
  );
};

export default NoResults;
