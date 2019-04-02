import { Omit } from "@material-ui/core";
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
import * as React from "react";
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
      left: 0,
      marginTop: theme.spacing.unit,
      position: "absolute",
      right: 0,
      zIndex: 1
    }
  });

interface SingleAutocompleteSelectFieldProps extends WithStyles<typeof styles> {
  error?: boolean;
  name: string;
  choices: Array<{
    label: string;
    value: any;
  }>;
  value?: {
    label: string;
    value: any;
  };
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  custom?: boolean;
  helperText?: string;
  label?: string;
  InputProps?: InputProps;
  fetchChoices?(value: string);
  onChange(event);
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
    custom,
    disabled,
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
  }: SingleAutocompleteSelectFieldProps) => {
    const handleChange = item => onChange({ target: { name, value: item } });

    return (
      <DebounceAutocomplete debounceFn={fetchChoices}>
        {debounceFn => (
          <Downshift
            selectedItem={value}
            itemToString={item => (item ? item.label : "")}
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
              const isCustom =
                choices && selectedItem
                  ? choices.filter(c => c.value === selectedItem.value)
                      .length === 0
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
                        <ArrowDropdownIcon
                          onClick={disabled ? undefined : toggleMenu}
                        />
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
                  {isOpen && (
                    <Paper className={classes.paper} square>
                      {loading ? (
                        <MenuItem disabled={true} component="div">
                          {i18n.t("Loading...")}
                        </MenuItem>
                      ) : choices.length > 0 || custom ? (
                        <>
                          {choices.map((suggestion, index) => (
                            <MenuItem
                              key={JSON.stringify(suggestion)}
                              selected={highlightedIndex === index}
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
