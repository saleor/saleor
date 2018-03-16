import * as React from "react";
import Chip from "material-ui/Chip";
import Select, { SelectProps } from "material-ui/Select";
import { FormControl, FormHelperText } from "material-ui/Form";
import { InputLabel } from "material-ui/Input";
import { MenuItem } from "material-ui/Menu";
import { withStyles } from "material-ui/styles";

const decorate = withStyles({
  formControl: {
    width: "100%"
  }
});

interface SingleSelectFieldProps {
  label: string;
  hint?: string;
  choices: Array<{
    value: string;
    label: string;
  }>;
  value: string;
  onChange(event: any);
  name: string;
  selectProps?: SelectProps;
}
export const SingleSelectField = decorate<SingleSelectFieldProps>(
  ({ classes, label, choices, value, onChange, name, hint, selectProps }) => {
    const choicesByKey = choices.reduce((prev, curr) => {
      prev[curr.value] = curr.label;
      return prev;
    }, {});

    return (
      <FormControl className={classes.formControl}>
        <InputLabel shrink={!!value}>{label}</InputLabel>
        <Select
          fullWidth
          renderValue={choiceValue =>
            choiceValue ? choicesByKey[choiceValue.toString()] : ""
          }
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

export default SingleSelectField;
