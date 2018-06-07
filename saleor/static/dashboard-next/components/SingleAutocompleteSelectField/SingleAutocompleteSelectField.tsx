import MenuItem from "@material-ui/core/MenuItem";
import Paper from "@material-ui/core/Paper";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Downshift from "downshift";
import * as React from "react";

import i18n from "../../i18n";

interface SingleAutocompleteSelectFieldProps {
  name: string;
  choices: Array<{
    label: string;
    value: string;
  }>;
  value?: {
    label: string;
    value: string;
  };
  loading?: boolean;
  placeholder?: string;
  custom?: boolean;
  helperText?: string;
  label?: string;
  fetchChoices(value: string);
  onChange(event);
}

const decorate = withStyles(theme => ({
  container: {
    flexGrow: 1,
    position: "relative" as "relative"
  },
  inputRoot: {
    flexWrap: "wrap" as "wrap"
  },
  paper: {
    left: 0,
    marginTop: theme.spacing.unit,
    position: "absolute" as "absolute",
    right: 0,
    zIndex: 1
  }
}));

export const SingleAutocompleteSelectField = decorate<
  SingleAutocompleteSelectFieldProps
>(
  ({
    choices,
    classes,
    custom,
    helperText,
    label,
    loading,
    name,
    placeholder,
    value,
    fetchChoices,
    onChange
  }) => {
    const handleChange = item => onChange({ target: { name, value: item } });

    return (
      <Downshift
        selectedItem={value}
        itemToString={item => (item ? item.label : "")}
        onSelect={handleChange}
        onInputValueChange={fetchChoices}
      >
        {({
          getInputProps,
          getItemProps,
          isOpen,
          inputValue,
          selectedItem,
          highlightedIndex
        }) => {
          const isCustom =
            choices.filter(c => c.value === selectedItem.value).length === 0;
          return (
            <div className={classes.container}>
              <TextField
                InputProps={{
                  classes: {
                    root: classes.inputRoot
                  },
                  ...getInputProps({
                    placeholder
                  })
                }}
                helperText={helperText}
                label={label}
                fullWidth={true}
              />
              {isOpen && (
                <Paper className={classes.paper} square>
                  {loading ? (
                    <MenuItem disabled={true} component="div">
                      {i18n.t("Loading...")}
                    </MenuItem>
                  ) : (
                    <>
                      {choices.map((suggestion, index) => (
                        <MenuItem
                          key={suggestion.value}
                          selected={suggestion.value === selectedItem.value}
                          component="div"
                          {...getItemProps({ item: suggestion })}
                        >
                          {suggestion.label}
                        </MenuItem>
                      ))}
                      {custom && (
                        <MenuItem
                          key={"customValue"}
                          selected={isCustom}
                          component="div"
                          {...getItemProps({
                            item: { label: inputValue, value: inputValue }
                          })}
                        >
                          {i18n.t("Add custom value")}
                        </MenuItem>
                      )}
                    </>
                  )}
                </Paper>
              )}
            </div>
          );
        }}
      </Downshift>
    );
  }
);
export default SingleAutocompleteSelectField;
