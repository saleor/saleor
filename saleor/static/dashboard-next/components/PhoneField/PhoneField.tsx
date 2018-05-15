import { withStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import * as React from "react";

import SingleSelectField from "../../components/SingleSelectField";

interface PhoneFieldProps {
  name: string;
  value: {
    prefix: string;
    number: string;
  };
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
  ({ classes, name, value, prefixes, label, onChange }) => (
    <div className={classes.root}>
      <SingleSelectField
        name={name}
        choices={prefixes.map(p => ({ label: "+" + p, value: p }))}
        onChange={onChange}
        value={value.prefix}
        label={label}
      />
      <TextField
        name={name}
        onChange={onChange}
        value={value.number}
        label="&nbsp;"
        type="number"
      />
    </div>
  )
);
export default PhoneField;
