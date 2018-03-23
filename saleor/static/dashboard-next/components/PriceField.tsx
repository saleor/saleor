import { FormControl, FormHelperText } from "material-ui/Form";
import Input, { InputAdornment, InputLabel } from "material-ui/Input";
import { withStyles } from "material-ui/styles";
import * as React from "react";

interface PriceFieldProps {
  currencySymbol: string;
  hint?: string;
  label: string;
  name: string;
  value: {
    max?: string;
    min?: string;
  };
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  inputContainer: {
    display: "grid",
    gridTemplateColumns: "calc(50% - 1rem) 2rem calc(50% - 1rem)"
  },
  maxInput: {
    marginTop: theme.spacing.unit * 2
  },
  separator: {
    marginTop: theme.spacing.unit * 3,
    textAlign: "center",
    width: "100%"
  },
  widgetContainer: {
    marginTop: theme.spacing.unit * 2
  }
}));

export const PriceField = decorate<PriceFieldProps>(
  ({ label, hint, currencySymbol, name, classes, onChange, value }) => (
    <div className={classes.widgetContainer}>
      <div className={classes.inputContainer}>
        <FormControl>
          <InputLabel htmlFor={`${name}_min`}>{label}</InputLabel>
          <Input
            value={value.min}
            endAdornment={
              <InputAdornment position="end">{currencySymbol}</InputAdornment>
            }
            fullWidth
            name={`${name}_min`}
            onChange={onChange}
            type="number"
          />
        </FormControl>
        <span className={classes.separator}>-</span>
        <FormControl>
          <Input
            value={value.max}
            endAdornment={
              <InputAdornment position="end">{currencySymbol}</InputAdornment>
            }
            className={classes.maxInput}
            fullWidth
            name={`${name}_max`}
            onChange={onChange}
            type="number"
          />
        </FormControl>
      </div>
      {hint && <FormHelperText>{hint}</FormHelperText>}
    </div>
  )
);

export default PriceField;
