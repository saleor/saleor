import * as React from 'react';

interface AttributeInputProps {
  checked?: boolean;
  attribute: any;
  value: any;
  onClick(name: string, value: any): any;
};

const AttributeInput = ({attribute, checked, onClick, value}: AttributeInputProps) => {
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

export default AttributeInput;
