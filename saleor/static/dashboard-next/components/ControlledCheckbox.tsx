import Checkbox from "material-ui/Checkbox";
import { FormControlLabel } from "material-ui/Form";
import * as React from "react";

interface ControlledCheckboxProps {
  name: string;
  label?: string;
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
        onChange={() => onChange({ target: { name, value: !checked } })}
        name={name}
      />
    }
    label={label}
  />
);

export default ControlledCheckbox;
