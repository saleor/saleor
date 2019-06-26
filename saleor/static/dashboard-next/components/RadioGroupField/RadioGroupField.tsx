import FormControl from "@material-ui/core/FormControl";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import FormHelperText from "@material-ui/core/FormHelperText";
import FormLabel from "@material-ui/core/FormLabel";
import MenuItem from "@material-ui/core/MenuItem";
import Radio from "@material-ui/core/Radio";
import RadioGroup from "@material-ui/core/RadioGroup";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";

const styles = createStyles({
  formControl: {
    padding: "0 15px",
    width: "100%"
  },
  formLabel: {
    marginLeft: "-5px",
    paddingBottom: "10px"
  },
  radioLabel: {
    "& > span": {
      padding: "6px"
    }
  }
});

interface RadioGroupFieldProps extends WithStyles<typeof styles> {
  choices: Array<{
    value: string;
    label: string | React.ReactNode;
  }>;
  className?: string;
  disabled?: boolean;
  error?: boolean;
  hint?: string;
  label?: string;
  name?: string;
  value?: string;
  onChange(event: any);
}

export const RadioGroupField = withStyles(styles, {
  name: "RadioGroupField"
})(
  ({
    className,
    classes,
    disabled,
    error,
    label,
    choices,
    value,
    onChange,
    name,
    hint
  }: RadioGroupFieldProps) => {
    return (
      <FormControl
        className={classNames(classes.formControl, className)}
        error={error}
        disabled={disabled}
      >
        <FormLabel className={classes.formLabel}>{label}</FormLabel>
        <RadioGroup
          aria-label={name}
          name={name}
          value={value}
          onChange={onChange}
        >
          {choices.length > 0 ? (
            choices.map(choice => (
              <FormControlLabel
                value={choice.value}
                className={classes.radioLabel}
                control={<Radio color="primary" />}
                label={choice.value}
                key={choice.value}
              />
            ))
          ) : (
            <MenuItem disabled={true}>{i18n.t("No results found")}</MenuItem>
          )}
        </RadioGroup>
        {hint && <FormHelperText>{hint}</FormHelperText>}
      </FormControl>
    );
  }
);
RadioGroupField.displayName = "RadioGroupField";
export default RadioGroupField;
