import * as React from 'react';
import * as InlineSVG from 'react-inlinesvg';

let loader = require<string>('../../images/loader.svg');

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
