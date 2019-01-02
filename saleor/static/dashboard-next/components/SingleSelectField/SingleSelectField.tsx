import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import InputLabel from "@material-ui/core/InputLabel";
import MenuItem from "@material-ui/core/MenuItem";
import Select, { SelectProps } from "@material-ui/core/Select";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import i18n from "../../i18n";

const styles = createStyles({
  formControl: {
    width: "100%"
  }
});

interface SingleSelectFieldProps extends WithStyles<typeof styles> {
  choices: Array<{
    value: string;
    label: string | React.ReactNode;
  }>;
  disabled?: boolean;
  error?: boolean;
  hint?: string;
  label?: string;
  name?: string;
  selectProps?: SelectProps;
  value?: string;
  onChange(event: any);
}

export const SingleSelectField = withStyles(styles, {
  name: "SingleSelectField"
})(
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
  }: SingleSelectFieldProps) => {
    const choicesByKey: { [key: string]: string } =
      choices === undefined
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
        <InputLabel shrink={!!value}>{label}</InputLabel>
        <Select
          fullWidth
          renderValue={choiceValue =>
            choiceValue ? choicesByKey[choiceValue.toString()] : ""
          }
          value={value || ""}
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
SingleSelectField.displayName = "SingleSelectField";
export default SingleSelectField;
