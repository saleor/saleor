import Chip from "@material-ui/core/Chip";
import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import InputLabel from "@material-ui/core/InputLabel";
import MenuItem from "@material-ui/core/MenuItem";
import Select, { SelectProps } from "@material-ui/core/Select";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import i18n from "../../i18n";

const decorate = withStyles(theme => ({
  chip: {
    margin: theme.spacing.unit * 0.5
  },
  chipContainer: {
    display: "flex",
    "flex-wrap": "wrap",
    marginLeft: -theme.spacing.unit * 0.5,
    marginRight: -theme.spacing.unit * 0.5
  },
  formControl: {
    width: "100%"
  }
}));

interface MultiSelectFieldProps {
  choices: Array<{
    value: string;
    label: string;
  }>;
  disabled?: boolean;
  error?: boolean;
  hint?: string;
  label?: string;
  name?: string;
  selectProps?: SelectProps;
  value?: string[];
  onChange(event: any);
}
export const MultiSelectField = decorate<MultiSelectFieldProps>(
  ({
    classes,
    disabled,
    error,
    label,
    choices,
    value,
    onChange,
    name,
    hint,
    selectProps
  }) => {
    const choicesByKey = disabled
      ? {}
      : choices.reduce((prev, curr) => {
          prev[curr.value] = curr.label;
          return prev;
        }, {});

    return (
      <FormControl
        className={classes.formControl}
        error={error}
        disabled={disabled}
      >
        {label && <InputLabel>{label}</InputLabel>}
        <Select
          multiple
          fullWidth
          renderValue={choiceValues => (
            <div className={classes.chipContainer}>
              {(choiceValues as string[]).map(choiceValue => (
                <Chip
                  key={choiceValue}
                  label={choicesByKey[choiceValue]}
                  className={classes.chip}
                />
              ))}
            </div>
          )}
          value={value}
          name={name}
          onChange={onChange}
          {...selectProps}
        >
          {choices.length > 0 ? (
            choices.map(choice => (
              <MenuItem value={choice.value} key={choice.value}>
                {choice.label}
              </MenuItem>
            ))
          ) : (
            <MenuItem disabled={true}>{i18n.t("No results found")}</MenuItem>
          )}
        </Select>
        {hint && <FormHelperText>{hint}</FormHelperText>}
      </FormControl>
    );
  }
);
MultiSelectField.defaultProps = {
  value: []
};

MultiSelectField.displayName = "MultiSelectField";
export default MultiSelectField;
