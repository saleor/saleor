import * as React from "react";
import Input, { InputLabel, InputAdornment } from "material-ui/Input";
import Typography from "material-ui/Typography";
import { FormControl, FormHelperText } from "material-ui/Form";
import { withStyles } from "material-ui/styles";

interface PriceFieldProps {
  label: string;
  hint?: string;
  currencySymbol: string;
  name: string;
  onChange(event: any);
  value: {
    min?: string;
    max?: string;
  };
}

const decorate = withStyles(theme => ({
  widgetContainer: {
    marginTop: theme.spacing.unit * 2
  },
  inputContainer: {
    display: "grid",
    gridTemplateColumns: "calc(50% - 1rem) 2rem calc(50% - 1rem)"
  },
  separator: {
    textAlign: "center",
    width: "100%",
    marginTop: theme.spacing.unit * 3
  },
  maxInput: {
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
            defaultValue={value.min}
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
            defaultValue={value.max}
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
