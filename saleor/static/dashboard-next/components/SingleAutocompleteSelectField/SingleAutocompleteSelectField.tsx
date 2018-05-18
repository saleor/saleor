import Downshift from "downshift";
import * as keycode from "keycode";
import Chip from "material-ui/Chip";
import { MenuItem } from "material-ui/Menu";
import Paper from "material-ui/Paper";
import { withStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import * as React from "react";

interface SingleAutocompleteSelectFieldProps {
  name: string;
  value?: {
    label: string;
    value: string;
  };
  loading?: boolean;
  fetchChoices(
    value: string
  ): Array<{
    label: string;
    value: string;
  }>;
  onChange(event);
}

const decorate = withStyles(theme => ({
  chip: {
    margin: `${theme.spacing.unit / 2}px ${theme.spacing.unit / 4}px`
  },
  container: {
    flexGrow: 1,
    position: "relative" as "absolute"
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
>(({ classes, name, value, fetchChoices, onChange }) => {
  const handleChange = item => onChange({ target: { name, value: item } });
  return (
    <Downshift
      selectedItem={value}
      itemToString={item => (item ? item.label : "")}
      onSelect={handleChange}
    >
      {({
        getInputProps,
        getItemProps,
        isOpen,
        inputValue,
        selectedItem,
        highlightedIndex
      }) => {
        const choices = fetchChoices(inputValue);
        return (
          <div className={classes.container}>
            <TextField
              InputProps={{
                classes: {
                  root: classes.inputRoot
                },
                ...getInputProps({
                  placeholder: "Search a country (start with a)"
                })
              }}
              fullWidth={true}
            />
            {isOpen ? (
              <Paper className={classes.paper} square>
                {choices.map((suggestion, index) => (
                  <MenuItem
                    key={suggestion.value}
                    selected={highlightedIndex === index}
                    component="div"
                    style={{
                      fontWeight:
                        (selectedItem.value || "").indexOf(suggestion.value) >
                        -1
                          ? 500
                          : 400
                    }}
                    {...getItemProps({ item: suggestion })}
                  >
                    {suggestion.label}
                  </MenuItem>
                ))}
              </Paper>
            ) : null}
          </div>
        );
      }}
    </Downshift>
  );
});
export default SingleAutocompleteSelectField;
