import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import Input from "@material-ui/core/Input";
import InputAdornment from "@material-ui/core/InputAdornment";
import InputLabel from "@material-ui/core/InputLabel";
import { withStyles } from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

interface PriceRangeFieldProps {
  currencySymbol: string;
  disabled?: boolean;
  error?: boolean;
  hint?: string;
  label?: string;
  name: string;
  value: {
    max: string | number;
    min: string | number;
  };
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  currencySymbol: {
    fontSize: "0.875rem"
  },
  inputContainer: {
    display: "grid",
    gridTemplateColumns: "1fr 2rem 1fr"
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

export const PriceRangeField = decorate<PriceRangeFieldProps>(
  ({
    disabled,
    error,
    label,
    hint,
    currencySymbol,
    name,
    classes,
    onChange,
    value
  }) => (
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
            className={classNames({ [classes.pullDown]: !label })}
            fullWidth
            name={`${name}_min`}
            onChange={onChange}
            type="number"
            disabled={disabled}
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
            disabled={disabled}
          />
        </FormControl>
      </div>
    </div>
  )
);
PriceRangeField.defaultProps = {
  name: "price"
};

interface PriceFieldProps {
  currencySymbol?: string;
  disabled?: boolean;
  error?: boolean;
  hint?: string;
  label?: string;
  name?: string;
  value?: string | number;
  onChange(event: any);
}

export const PriceField = decorate<PriceFieldProps>(
  ({
    disabled,
    error,
    label,
    hint,
    currencySymbol,
    name,
    classes,
    onChange,
    value
  }) => (
    <FormControl error={error} fullWidth>
      {label && <InputLabel htmlFor={name}>{label}</InputLabel>}
      <Input
        value={value || ""}
        endAdornment={
          currencySymbol ? (
            <InputAdornment position="end" className={classes.currencySymbol}>
              {currencySymbol}
            </InputAdornment>
          ) : (
            <span />
          )
        }
        name={name}
        onChange={onChange}
        type="number"
        disabled={disabled}
      />
      {hint && <FormHelperText>{hint}</FormHelperText>}
    </FormControl>
  )
);
PriceField.defaultProps = {
  name: "price"
};

PriceField.displayName = "PriceField";
export default PriceField;
