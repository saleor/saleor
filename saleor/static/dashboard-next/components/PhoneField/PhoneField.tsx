import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import SingleSelectField from "../../components/SingleSelectField";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridTemplateColumns: "5rem 1fr"
    }
  });

interface PhoneFieldProps extends WithStyles<typeof styles> {
  name: string;
  prefix: string;
  number: string;
  prefixes: string[];
  label?: string;
  onChange(event: React.ChangeEvent<any>);
}

const PhoneField = withStyles(styles, { name: "PhoneField" })(
  ({
    classes,
    name,
    number: phoneNumber,
    prefix,
    prefixes,
    label,
    onChange
  }: PhoneFieldProps) => (
    <div className={classes.root}>
      <SingleSelectField
        name={name + "_prefix"}
        choices={prefixes.map(p => ({ label: "+" + p, value: p }))}
        onChange={onChange}
        value={prefix}
        label={label}
      />
      <TextField
        name={name + "_number"}
        onChange={onChange}
        value={phoneNumber}
        label="&nbsp;"
      />
    </div>
  )
);
PhoneField.displayName = "PhoneField";
export default PhoneField;
