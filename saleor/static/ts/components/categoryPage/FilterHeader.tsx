import * as React from 'react';

import * as InlineSVG from 'react-inlinesvg';

let chevronUpIcon = require<string>('../../../images/chevron-up-icon.svg');
let chevronDownIcon = require<string>('../../../images/chevron-down-icon.svg');

interface FilterHeaderProps {
  onClick(): any;
  title: string;
  visibility?: boolean;
};

const FilterHeader = ({ onClick, title, visibility }: FilterHeaderProps) => {
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

export default FilterHeader;
