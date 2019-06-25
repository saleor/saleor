import CircularProgress from "@material-ui/core/CircularProgress";
import MenuItem from "@material-ui/core/MenuItem";
import Paper from "@material-ui/core/Paper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Downshift, { ControllerStateAndHelpers } from "downshift";
import React from "react";
import { compareTwoStrings } from "string-similarity";

import Checkbox from "@saleor/components/Checkbox";
import Debounce, { DebounceProps } from "@saleor/components/Debounce";
import i18n from "@saleor/i18n";
import ArrowDropdownIcon from "@saleor/icons/ArrowDropdown";

export interface MultiAutocompleteChoiceType {
  label: string;
  value: string;
}

const styles = (theme: Theme) =>
  createStyles({
    chip: {
      margin: `${theme.spacing.unit / 2}px ${theme.spacing.unit / 2}px`
    },
    container: {
      flexGrow: 1,
      position: "relative"
    },
    paper: {
      left: 0,
      marginTop: theme.spacing.unit,
      padding: theme.spacing.unit,
      position: "absolute",
      right: 0,
      zIndex: 2
    }
  });

export interface MultiAutocompleteSelectFieldProps {
  displayValue: string;
  name: string;
  choices: MultiAutocompleteChoiceType[];
  value: string[];
  loading?: boolean;
  placeholder?: string;
  helperText?: string;
  label?: string;
  fetchChoices?(value: string);
  onChange(event);
}

const DebounceAutocomplete: React.ComponentType<
  DebounceProps<string>
> = Debounce;

export const MultiAutocompleteSelectFieldComponent = withStyles(styles, {
  name: "MultiAutocompleteSelectField"
})(
  ({
    choices,
    classes,
    displayValue,
    helperText,
    label,
    loading,
    name,
    placeholder,
    value,
    fetchChoices,
    onChange
  }: MultiAutocompleteSelectFieldProps & WithStyles<typeof styles>) => {
    const [focused, setFocus] = React.useState(false);
    const handleSelect = (
      item: MultiAutocompleteChoiceType,
      { reset }: ControllerStateAndHelpers
    ) => {
      reset({ inputValue: "" });
      onChange({ target: { name, value: item } });
    };

    return (
      <Downshift
        selectedItem={value}
        itemToString={item => (item ? item.label : "")}
        onSelect={handleSelect}
        onInputValueChange={fetchChoices}
      >
        {({
          getInputProps,
          getItemProps,
          isOpen,
          toggleMenu,
          openMenu,
          highlightedIndex,
          inputValue
        }) => {
          return (
            <div className={classes.container}>
              <TextField
                InputProps={{
                  ...getInputProps({
                    placeholder,
                    value: focused ? inputValue : displayValue
                  }),
                  endAdornment: (
                    <div>
                      {loading ? (
                        <CircularProgress size={20} />
                      ) : (
                        <ArrowDropdownIcon onClick={toggleMenu} />
                      )}
                    </div>
                  ),
                  id: undefined,
                  onBlur: () => setFocus(false),
                  onFocus: () => {
                    openMenu();
                    setFocus(true);
                  }
                }}
                helperText={helperText}
                label={label}
                fullWidth={true}
              />
              {isOpen && (
                <Paper className={classes.paper} square>
                  {!loading && choices.length > 0
                    ? choices.map((suggestion, index) => (
                        <MenuItem
                          key={suggestion.value}
                          selected={highlightedIndex === index}
                          component="div"
                          {...getItemProps({
                            item: suggestion.value
                          })}
                        >
                          <Checkbox
                            checked={value.includes(suggestion.value)}
                            disableRipple
                          />
                          {suggestion.label}
                        </MenuItem>
                      ))
                    : !loading && (
                        <MenuItem disabled={true} component="div">
                          {i18n.t("No results found")}
                        </MenuItem>
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
const MultiAutocompleteSelectField: React.FC<
  MultiAutocompleteSelectFieldProps
> = ({ choices, fetchChoices, ...props }) => {
  const [query, setQuery] = React.useState("");
  if (fetchChoices) {
    return (
      <DebounceAutocomplete debounceFn={fetchChoices}>
        {debounceFn => (
          <MultiAutocompleteSelectFieldComponent
            choices={choices}
            {...props}
            fetchChoices={debounceFn}
          />
        )}
      </DebounceAutocomplete>
    );
  }

  const sortedChoices = choices.sort((a, b) => {
    const ratingA = compareTwoStrings(query, a.label);
    const ratingB = compareTwoStrings(query, b.label);
    if (ratingA > ratingB) {
      return -1;
    }
    if (ratingA < ratingB) {
      return 1;
    }
    return 0;
  });

  return (
    <MultiAutocompleteSelectFieldComponent
      fetchChoices={q => setQuery(q || "")}
      choices={sortedChoices}
      {...props}
    />
  );
};
MultiAutocompleteSelectField.displayName = "MultiAutocompleteSelectField";
export default MultiAutocompleteSelectField;
