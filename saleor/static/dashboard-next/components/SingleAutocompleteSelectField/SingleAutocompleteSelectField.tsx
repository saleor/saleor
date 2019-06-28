import { Omit } from "@material-ui/core";
import CircularProgress from "@material-ui/core/CircularProgress";
import { InputProps } from "@material-ui/core/Input";
import MenuItem from "@material-ui/core/MenuItem";
import Paper from "@material-ui/core/Paper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Downshift from "downshift";
import React from "react";
import { compareTwoStrings } from "string-similarity";

import i18n from "../../i18n";
import ArrowDropdownIcon from "../../icons/ArrowDropdown";
import Debounce, { DebounceProps } from "../Debounce";

const styles = (theme: Theme) =>
  createStyles({
    container: {
      flexGrow: 1,
      position: "relative"
    },
    paper: {
      borderRadius: 4,
      left: 0,
      marginTop: theme.spacing.unit,
      padding: 8,
      position: "absolute",
      right: 0,
      zIndex: 2
    }
  });

export interface SingleAutocompleteChoiceType {
  label: string;
  value: any;
}
export interface SingleAutocompleteSelectFieldProps {
  error?: boolean;
  name: string;
  displayValue: string;
  choices: SingleAutocompleteChoiceType[];
  value?: string;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  allowCustomValues?: boolean;
  helperText?: string;
  label?: string;
  InputProps?: InputProps;
  fetchChoices?: (value: string) => void;
  onChange: (event: React.ChangeEvent<any>) => void;
}

interface SingleAutocompleteSelectFieldState {
  choices: Array<{
    label: string;
    value: string;
  }>;
}

const DebounceAutocomplete: React.ComponentType<
  DebounceProps<string>
> = Debounce;

const SingleAutocompleteSelectFieldComponent = withStyles(styles, {
  name: "SingleAutocompleteSelectField"
})(
  ({
    choices,
    classes,
    allowCustomValues: custom,
    disabled,
    displayValue,
    error,
    helperText,
    label,
    loading,
    name,
    placeholder,
    value,
    InputProps,
    fetchChoices,
    onChange
  }: SingleAutocompleteSelectFieldProps & WithStyles<typeof styles>) => {
    const handleChange = item =>
      onChange({
        target: {
          name,
          value: item
        }
      } as any);

    return (
      <DebounceAutocomplete debounceFn={fetchChoices}>
        {debounceFn => (
          <Downshift
            selectedItem={value}
            itemToString={() => displayValue}
            onSelect={handleChange}
            onInputValueChange={value => debounceFn(value)}
          >
            {({
              getInputProps,
              getItemProps,
              isOpen,
              inputValue,
              selectedItem,
              toggleMenu,
              openMenu,
              closeMenu,
              highlightedIndex
            }) => {
              const isCustomValueSelected =
                choices && selectedItem
                  ? choices.filter(c => c.value === selectedItem).length === 0
                  : false;

              return (
                <div className={classes.container}>
                  <TextField
                    InputProps={{
                      ...InputProps,
                      ...getInputProps({
                        placeholder
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
                      error,
                      id: undefined,
                      onBlur: closeMenu,
                      onFocus: openMenu
                    }}
                    disabled={disabled}
                    helperText={helperText}
                    label={label}
                    fullWidth={true}
                  />
                  {isOpen && (inputValue || choices.length) && (
                    <Paper className={classes.paper} square>
                      {choices.length > 0 || custom ? (
                        <>
                          {choices.map((suggestion, index) => (
                            <MenuItem
                              key={JSON.stringify(suggestion)}
                              selected={
                                highlightedIndex === index ||
                                selectedItem === suggestion.value
                              }
                              component="div"
                              {...getItemProps({ item: suggestion.value })}
                            >
                              {suggestion.label}
                            </MenuItem>
                          ))}
                          {custom &&
                            inputValue &&
                            !choices.find(
                              choice =>
                                choice.label.toLowerCase() ===
                                inputValue.toLowerCase()
                            ) && (
                              <MenuItem
                                key={"customValue"}
                                selected={isCustomValueSelected}
                                component="div"
                                {...getItemProps({
                                  item: inputValue
                                })}
                              >
                                {i18n.t("Add new value: {{ value }}", {
                                  context: "add custom option",
                                  value: inputValue
                                })}
                              </MenuItem>
                            )}
                        </>
                      ) : (
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
        )}
      </DebounceAutocomplete>
    );
  }
);

export class SingleAutocompleteSelectField extends React.Component<
  Omit<SingleAutocompleteSelectFieldProps, "classes">,
  SingleAutocompleteSelectFieldState
> {
  state = { choices: this.props.choices };

  handleInputChange = (value: string) =>
    this.setState((_, props) => ({
      choices: props.choices
        .sort((a, b) => {
          const ratingA = compareTwoStrings(value || "", a.label);
          const ratingB = compareTwoStrings(value || "", b.label);
          if (ratingA > ratingB) {
            return -1;
          }
          if (ratingA < ratingB) {
            return 1;
          }
          return 0;
        })
        .slice(0, 5)
    }));

  render() {
    if (!!this.props.fetchChoices) {
      return <SingleAutocompleteSelectFieldComponent {...this.props} />;
    }
    return (
      <SingleAutocompleteSelectFieldComponent
        {...this.props}
        choices={this.state.choices}
        fetchChoices={this.handleInputChange}
      />
    );
  }
}
export default SingleAutocompleteSelectField;
