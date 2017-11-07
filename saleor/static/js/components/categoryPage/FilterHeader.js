import React, { PropTypes } from 'react';

import InlineSVG from 'react-inlinesvg';

import chevronUpIcon from '../../../images/chevron_up.svg';
import chevronDownIcon from '../../../images/chevron_down.svg';

const FilterHeader = ({ onClick, title, visibility }) => {
  const imageSrc = visibility ? (chevronUpIcon) : (chevronDownIcon);
  const key = visibility ? 'chevronUpIcon' : 'chevronDownIcon';
  return (
    <h3 onClick={onClick}>
      {title}
      <div className="collapse-filters-icon">
        <InlineSVG key={key} src={imageSrc} />
      </div>
    </h3>
  );
};

FilterHeader.propTypes = {
  onClick: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  visibility: PropTypes.bool
};

export default FilterHeader;
