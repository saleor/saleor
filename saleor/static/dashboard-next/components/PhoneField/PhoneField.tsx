import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import SingleSelectField from "../../components/SingleSelectField";

interface PhoneFieldProps {
  name: string;
  prefix: string;
  number: string;
  prefixes: string[];
  label?: string;
  onChange(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "5rem 1fr"
  }
}));
const PhoneField = decorate<PhoneFieldProps>(
  ({
    classes,
    name,
    number: phoneNumber,
    prefix,
    prefixes,
    label,
    onChange
  }) => (
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
