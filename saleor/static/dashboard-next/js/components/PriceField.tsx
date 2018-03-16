import * as React from "react";
import Input, { InputLabel } from "material-ui/Input";
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
  widgetGrid: {
    display: "grid",
    gridTemplateColumns: "calc(100% - 3rem) 3rem",
    marginTop: theme.spacing.unit * 2
  },
  inputContainer: {
    display: "grid",
    gridTemplateColumns: "calc(50% - 1rem) 2rem calc(50% - 1rem)"
  },
  separator: {
    textAlign: "center",
    width: "100%",
    marginTop: theme.spacing.unit
  },
  currency: {
    marginTop: theme.spacing.unit,
    textAlign: "right"
  }
}));
export const PriceField = decorate<PriceFieldProps>(
  ({ label, hint, currencySymbol, name, classes, onChange, value }) => (
    <FormControl>
      <InputLabel htmlFor={`${name}_min`}>{label}</InputLabel>
      <div className={classes.widgetGrid}>
        <div className={classes.inputContainer}>
          <div>
            <Input
              name={`${name}_min`}
              fullWidth
              onChange={onChange}
              value={value.min}
            />
          </div>
          <span className={classes.separator}>-</span>
          <div>
            <Input
              name={`${name}_max`}
              fullWidth
              onChange={onChange}
              value={value.max}
            />
          </div>
        </div>
        <Typography variant="body1" className={classes.currency}>
          {currencySymbol}
        </Typography>
      </div>
      {hint && <FormHelperText>{hint}</FormHelperText>}
    </FormControl>
  )
);

export default PriceField;
