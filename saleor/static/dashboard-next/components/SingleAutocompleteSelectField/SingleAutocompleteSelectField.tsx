import Downshift from "downshift";
import * as keycode from "keycode";
import Chip from "material-ui/Chip";
import { MenuItem } from "material-ui/Menu";
import Paper from "material-ui/Paper";
import { CircularProgress } from "material-ui/Progress";
import { withStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import * as React from "react";

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
  fetchChoices(value: string);
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
>(
  ({
    classes,
    choices,
    name,
    placeholder,
    loading,
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
          return (
            <div className={classes.container}>
              <TextField
                InputProps={{
                  classes: {
                    root: classes.inputRoot
                  },
                  endAdornment: loading ? (
                    <CircularProgress size={20} style={{ marginTop: 3 }} />
                  ) : null,
                  ...getInputProps({
                    placeholder
                  })
                }}
                fullWidth={true}
              />
              {isOpen && !loading ? (
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
  }
);
export default SingleAutocompleteSelectField;
