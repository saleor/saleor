import { createStyles, Theme, withStyles, WithStyles } from "@material-ui/core";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import Switch from "@material-ui/core/Switch";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    label: {
      marginLeft: theme.spacing.unit * 2
    }
  });

interface ControlledSwitchProps extends WithStyles<typeof styles> {
  checked: boolean;
  disabled?: boolean;
  label: string | React.ReactNode;
  name: string;
  uncheckedLabel?: string | React.ReactNode;
  onChange?(event: React.ChangeEvent<any>);
}

export const ControlledSwitch = withStyles(styles, {
  name: "ControlledSwitch"
})(
  ({
    classes,
    checked,
    disabled,
    onChange,
    label,
    name,
    uncheckedLabel
  }: ControlledSwitchProps) => (
    <FormControlLabel
      control={
        <Switch
          onChange={() =>
            onChange({ target: { name, value: !checked } } as any)
          }
          checked={checked}
          color="primary"
          name={name}
        />
      }
      label={
        <div className={classes.label}>
          {uncheckedLabel ? (checked ? label : uncheckedLabel) : label}
        </div>
      }
      disabled={disabled}
    />
  )
);
ControlledSwitch.displayName = "ControlledSwitch";
export default ControlledSwitch;
