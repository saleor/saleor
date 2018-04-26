import { FormControlLabel } from "material-ui/Form";
import Switch from "material-ui/Switch";
import * as React from "react";

interface ControlledSwitchProps {
  checked: boolean;
  disabled?: boolean;
  uncheckedLabel?: string;
  label: string;
  onChange?(event: React.ChangeEvent<any>);
}

export const ControlledSwitch: React.StatelessComponent<
  ControlledSwitchProps
> = ({ checked, disabled, onChange, label, uncheckedLabel }) => (
  <FormControlLabel
    control={<Switch onChange={onChange} checked={checked} color="primary" />}
    label={uncheckedLabel ? (checked ? label : uncheckedLabel) : label}
    disabled={disabled}
  />
);
export default ControlledSwitch;
