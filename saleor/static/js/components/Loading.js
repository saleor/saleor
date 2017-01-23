import React from 'react';
import InlineSVG from 'react-inlinesvg';

import loader from '../../images/loader.svg';

const Loading = () => {
  return (
    <div className="row loader">
      <div className="col-12">
        <InlineSVG src={loader} />
      </div>
    </div>
  );
};

export default Loading;
