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
import Typography from "@material-ui/core/Typography";
import Downshift from "downshift";
import React from "react";
import { compareTwoStrings } from "string-similarity";

import useStateFromProps from "@saleor/hooks/useStateFromProps";
import i18n from "../../i18n";
import ArrowDropdownIcon from "../../icons/ArrowDropdown";
import Debounce, { DebounceProps } from "../Debounce";

const styles = (theme: Theme) =>
  createStyles({
    container: {
      flexGrow: 1,
      position: "relative"
    },
    menuItem: {
      height: "auto",
      whiteSpace: "normal"
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
  emptyOption?: boolean;
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
    allowCustomValues,
    disabled,
    displayValue,
    emptyOption,
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
    const [prevDisplayValue] = useStateFromProps(displayValue);
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
            defaultInputValue={displayValue}
            itemToString={() => displayValue}
            onInputValueChange={value => debounceFn(value)}
            onSelect={handleChange}
            selectedItem={value}
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
              highlightedIndex,
              reset
            }) => {
              const isCustomValueSelected =
                choices && selectedItem
                  ? choices.filter(c => c.value === selectedItem).length === 0
                  : false;

              if (prevDisplayValue !== displayValue) {
                reset({ inputValue: displayValue });
              }

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
                  {isOpen && (!!inputValue || !!choices.length) && (
                    <Paper className={classes.paper} square>
                      {choices.length > 0 || allowCustomValues ? (
                        <>
                          {emptyOption && (
                            <MenuItem
                              className={classes.menuItem}
                              component="div"
                              {...getItemProps({
                                item: ""
                              })}
                            >
                              <Typography color="textSecondary">
                                {i18n.t("None")}
                              </Typography>
                            </MenuItem>
                          )}
                          {choices.map((suggestion, index) => {
                            const choiceIndex = index + (emptyOption ? 1 : 0);

                            return (
                              <MenuItem
                                className={classes.menuItem}
                                key={JSON.stringify(suggestion)}
                                selected={
                                  highlightedIndex === choiceIndex ||
                                  selectedItem === suggestion.value
                                }
                                component="div"
                                {...getItemProps({
                                  index: choiceIndex,
                                  item: suggestion.value
                                })}
                              >
                                {suggestion.label}
                              </MenuItem>
                            );
                          })}
                          {allowCustomValues &&
                            !!inputValue &&
                            !choices.find(
                              choice =>
                                choice.label.toLowerCase() ===
                                inputValue.toLowerCase()
                            ) && (
                              <MenuItem
                                className={classes.menuItem}
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
