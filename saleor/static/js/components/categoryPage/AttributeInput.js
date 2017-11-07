import React, { PropTypes } from 'react';

const AttributeInput = ({attribute, checked, onClick, value}) => {
  const handleChange = (event) => {
    const { name, value } = event.target;
    onClick(name, value);
  };

  return (
    <label>
      <input
        checked={checked}
        name={attribute.slug}
        onChange={handleChange}
        type="checkbox"
        value={value.slug}
      />
      {value.name}
    </label>
  );
};

AttributeInput.propTypes = {
  checked: PropTypes.bool,
  attribute: PropTypes.object.isRequired,
  value: PropTypes.object.isRequired,
  onClick: PropTypes.func.isRequired
};

export default AttributeInput;
