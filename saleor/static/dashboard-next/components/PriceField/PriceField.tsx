import { FormControl, FormHelperText } from "material-ui/Form";
import Input, { InputAdornment, InputLabel } from "material-ui/Input";
import { withStyles } from "material-ui/styles";
import * as React from "react";

interface PriceFieldProps {
  currencySymbol?: string;
  error?: boolean;
  hint?: string;
  label?: string;
  name?: string;
  value?: {
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
  pullDown: {
    marginTop: theme.spacing.unit * 2
  },
  separator: {
    marginTop: theme.spacing.unit * 3,
    textAlign: "center" as "center",
    width: "100%"
  },
  widgetContainer: {
    marginTop: theme.spacing.unit * 2
  }
}));

export const PriceField = decorate<PriceFieldProps>(
  ({ error, label, hint, currencySymbol, name, classes, onChange, value }) => (
    <div className={classes.widgetContainer}>
      <div className={classes.inputContainer}>
        <FormControl error={error}>
          {label && <InputLabel htmlFor={`${name}_min`}>{label}</InputLabel>}
          <Input
            value={value ? value.min : ""}
            endAdornment={
              currencySymbol ? (
                <InputAdornment position="end">{currencySymbol}</InputAdornment>
              ) : (
                <span />
              )
            }
            className={label ? "" : classes.pullDown}
            fullWidth
            name={`${name}_min`}
            onChange={onChange}
            type="number"
          />
          {hint && <FormHelperText>{hint}</FormHelperText>}
        </FormControl>
        <span className={classes.separator}>-</span>
        <FormControl error={error}>
          <Input
            value={value ? value.max : ""}
            endAdornment={
              currencySymbol ? (
                <InputAdornment position="end">{currencySymbol}</InputAdornment>
              ) : (
                <span />
              )
            }
            className={classes.pullDown}
            fullWidth
            name={`${name}_max`}
            onChange={onChange}
            type="number"
          />
        </FormControl>
      </div>
    </div>
  )
);
PriceField.defaultProps = {
  name: "price"
};

export default PriceField;
