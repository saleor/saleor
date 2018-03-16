import * as React from "react";
import Chip from "material-ui/Chip";
import Select, { SelectProps } from "material-ui/Select";
import { FormControl, FormHelperText } from "material-ui/Form";
import { InputLabel } from "material-ui/Input";
import { MenuItem } from "material-ui/Menu";
import { withStyles } from "material-ui/styles";

const decorate = withStyles(theme => ({
  chipContainer: {
    display: "flex",
    "flex-wrap": "wrap",
    marginTop: -theme.spacing.unit * 2,
    marginLeft: -theme.spacing.unit * 0.5,
    marginRight: -theme.spacing.unit * 0.5
  },
  chip: {
    margin: theme.spacing.unit * 0.5
  },
  formControl: {
    // marginTop: theme.spacing.unit * 2,
    width: "100%"
  }
}));

interface MultiSelectFieldProps {
  label: string;
  hint?: string;
  choices: Array<{
    value: string;
    label: string;
  }>;
  value: Array<string>;
  onChange(event: any);
  name: string;
  selectProps?: SelectProps;
}
export const MultiSelectField = decorate<MultiSelectFieldProps>(
  ({ classes, label, choices, value, onChange, name, hint, selectProps }) => {
    const choicesByKey = choices.reduce((prev, curr) => {
      prev[curr.value] = curr.label;
      return prev;
    }, {});

    return (
      <FormControl className={classes.formControl}>
        <InputLabel>{label}</InputLabel>
        <Select
          multiple
          fullWidth
          renderValue={choiceValues => (
            <div className={classes.chipContainer}>
              {(choiceValues as Array<string>).map(choiceValue => (
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
          {choices.map(choice => (
            <MenuItem value={choice.value} key={choice.value}>
              {choice.label}
            </MenuItem>
          ))}
        </Select>
        {hint && <FormHelperText>{hint}</FormHelperText>}
      </FormControl>
    );
  }
);

export default MultiSelectField;
