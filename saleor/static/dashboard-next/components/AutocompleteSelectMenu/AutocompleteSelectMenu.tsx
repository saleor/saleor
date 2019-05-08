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
import ArrowBack from "@material-ui/icons/ArrowBack";
import Downshift from "downshift";
import * as React from "react";

import i18n from "../../i18n";
import Debounce, { DebounceProps } from "../Debounce";

export interface SelectMenuItem {
  children?: SelectMenuItem[];
  label: React.ReactNode;
  value?: string;
}

export interface AutocompleteSelectMenuProps {
  disabled: boolean;
  displayValue: string;
  error: boolean;
  helperText: string;
  label: string;
  loading: boolean;
  name: string;
  options: SelectMenuItem[];
  placeholder: string;
  onChange: (event: React.ChangeEvent<any>) => void;
  onInputChange?: (value: string) => void;
}

function getOptionValues(option: SelectMenuItem): string[] {
  return option.value
    ? [option.value]
    : option.children.reduce(
        (acc, option) => [...acc, ...getOptionValues(option)],
        []
      );
}

export function validateOptions(options: SelectMenuItem[]): boolean {
  const values: string[] = options.reduce(
    (acc, option) => [...acc, ...getOptionValues(option)],
    []
  );
  const uniqueValues = Array.from(new Set(values));
  return uniqueValues.length === values.length;
}

const validationError: Error = new Error(
  "Values supplied to AutocompleteSelectMenu should be unique"
);

function getMenu(options: SelectMenuItem[], path: number[]): SelectMenuItem[] {
  if (path.length === 0) {
    return options;
  }
  return getMenu(options[path[0]].children, path.slice(1));
}

const DebounceAutocomplete: React.ComponentType<
  DebounceProps<string>
> = Debounce;

const styles = (theme: Theme) =>
  createStyles({
    container: {
      flexGrow: 1,
      position: "relative"
    },
    menuBack: {
      marginLeft: -theme.spacing.unit / 2,
      marginRight: theme.spacing.unit
    },
    paper: {
      left: 0,
      marginTop: theme.spacing.unit,
      position: "absolute",
      right: 0,
      zIndex: 1
    },
    root: {}
  });
const AutocompleteSelectMenu = withStyles(styles, {
  name: "AutocompleteSelectMenu"
})(
  ({
    classes,
    disabled,
    displayValue,
    error,
    helperText,
    label,
    loading,
    name,
    options,
    placeholder,
    onChange,
    onInputChange
  }: AutocompleteSelectMenuProps & WithStyles<typeof styles>) => {
    const [inputValue, setInputValue] = React.useState(displayValue || "");
    const [menuPath, setMenuPath] = React.useState<number[]>([]);

    const handleChange = (value: string) => {
      onChange({
        target: {
          name,
          value
        }
      } as any);
    };

    // Validate if option values are duplicated
    React.useEffect(() => {
      if (!validateOptions(options)) {
        throw validationError;
      }
    }, []);

    // Navigate back to main menu after input field change
    React.useEffect(() => setMenuPath([]), [JSON.stringify(options)]);

    // Reset input value after displayValue change
    React.useEffect(() => setInputValue(displayValue), [displayValue]);

    return (
      <DebounceAutocomplete debounceFn={onInputChange}>
        {debounceFn => (
          <Downshift
            itemToString={item => (item ? item.label : "")}
            onSelect={handleChange}
          >
            {({ getItemProps, isOpen, openMenu, closeMenu, selectItem }) => {
              return (
                <div className={classes.container}>
                  <TextField
                    InputProps={{
                      endAdornment: loading && <CircularProgress size={16} />,
                      id: undefined,
                      onBlur: () => {
                        closeMenu();
                        setMenuPath([]);
                        setInputValue(displayValue);
                      },
                      onChange: event => {
                        debounceFn(event.target.value);
                        setInputValue(event.target.value);
                      },
                      onFocus: () => openMenu(),
                      placeholder
                    }}
                    disabled={disabled}
                    error={error}
                    helperText={helperText}
                    label={label}
                    fullWidth={true}
                    value={inputValue}
                  />
                  {isOpen && (
                    <Paper className={classes.paper} square>
                      {menuPath.length > 0 && (
                        <MenuItem
                          component="div"
                          {...getItemProps({
                            item: null
                          })}
                          onClick={() =>
                            setMenuPath(menuPath.slice(0, menuPath.length - 2))
                          }
                        >
                          <ArrowBack className={classes.menuBack} />
                          {i18n.t("Back")}
                        </MenuItem>
                      )}
                      {getMenu(options, menuPath).map((suggestion, index) => (
                        <MenuItem
                          key={suggestion.label.toString() + suggestion.value}
                          component="div"
                          {...getItemProps({ item: suggestion })}
                          onClick={() =>
                            suggestion.value
                              ? selectItem(suggestion.value)
                              : setMenuPath([...menuPath, index])
                          }
                        >
                          {suggestion.label}
                        </MenuItem>
                      ))}
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
AutocompleteSelectMenu.displayName = "AutocompleteSelectMenu";
export default AutocompleteSelectMenu;
