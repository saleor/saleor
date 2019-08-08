import FormControlLabel from "@material-ui/core/FormControlLabel";
import React from "react";

import Checkbox from "./Checkbox";

interface ControlledCheckboxProps {
  name: string;
  label?: React.ReactNode;
  checked: boolean;
  disabled?: boolean;
  onChange(event: any);
}

export const ControlledCheckbox: React.StatelessComponent<
  ControlledCheckboxProps
> = ({ checked, disabled, name, label, onChange }) => (
  <FormControlLabel
    disabled={disabled}
    control={
      <Checkbox
        checked={checked}
        name={name}
        disableClickPropagation
        onChange={() => onChange({ target: { name, value: !checked } })}
      />
    }
    label={label}
  />
);
ControlledCheckbox.displayName = "ControlledCheckbox";
export default ControlledCheckbox;
