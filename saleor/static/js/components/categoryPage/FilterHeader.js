import * as PropTypes from 'prop-types';
import React from 'react';

import chevronDownIcon from '../../../images/chevron-down.svg';

const FilterHeader = ({ onClick, title }) => {
  const imageSrc = chevronDownIcon;
  const key = 'chevronDownIcon';
  return (
    <div className="filter-section__header" onClick={onClick}>
      <h3>
        {title}
      </h3>
      <div className="filter-section__icon">
        <img key={key} src={imageSrc} />
      </div>
    </div>
  );
};

FilterHeader.propTypes = {
  onClick: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired
};

export default FilterHeader;
