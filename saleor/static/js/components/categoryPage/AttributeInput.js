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
        name={attribute.name}
        onChange={handleChange}
        type="checkbox"
        value={value.slug}
      />
      {value.display}
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
