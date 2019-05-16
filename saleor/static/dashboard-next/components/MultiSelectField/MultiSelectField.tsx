import FilledInput from "@material-ui/core/FilledInput";
import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import InputLabel from "@material-ui/core/InputLabel";
import MenuItem from "@material-ui/core/MenuItem";
import Select, { SelectProps } from "@material-ui/core/Select";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import i18n from "../../i18n";
import Checkbox from "../Checkbox";

const styles = (theme: Theme) =>
  createStyles({
    checkbox: {
      marginRight: -theme.spacing.unit * 2
    },
    formControl: {
      width: "100%"
    },
    menuItem: {
      alignItems: "center",
      display: "flex",
      justifyContent: "space-between",
      width: "100%"
    }
  });

interface MultiSelectFieldProps extends WithStyles<typeof styles> {
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

export const MultiSelectField = withStyles(styles, {
  name: "MultiSelectField"
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
  }: MultiSelectFieldProps) => {
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
          renderValue={choiceValues =>
            (choiceValues as string[])
              .map(choiceValue => choicesByKey[choiceValue])
              .join(", ")
          }
          value={value}
          name={name}
          onChange={onChange}
          input={<FilledInput name={name} />}
          {...selectProps}
        >
          {choices.length > 0 ? (
            choices.map(choice => {
              const isSelected = !!value.find(
                selectedChoice => selectedChoice === choice.value
              );

              return (
                <MenuItem value={choice.value} key={choice.value}>
                  <div className={classes.menuItem}>
                    <span>{choice.label}</span>
                    <Checkbox
                      className={classes.checkbox}
                      checked={isSelected}
                      disableRipple={true}
                      disableTouchRipple={true}
                    />
                  </div>
                </MenuItem>
              );
            })
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
