import CircularProgress from "@material-ui/core/CircularProgress";
import IconButton from "@material-ui/core/IconButton";
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
import CloseIcon from "@material-ui/icons/Close";
import Downshift, { ControllerStateAndHelpers } from "downshift";
import React from "react";
import { compareTwoStrings } from "string-similarity";

import { fade } from "@material-ui/core/styles/colorManipulator";
import Checkbox from "@saleor/components/Checkbox";
import Debounce, { DebounceProps } from "@saleor/components/Debounce";
import i18n from "@saleor/i18n";
import ArrowDropdownIcon from "@saleor/icons/ArrowDropdown";
import Hr from "../Hr";

export interface MultiAutocompleteChoiceType {
  label: string;
  value: string;
}

const styles = (theme: Theme) =>
  createStyles({
    chip: {
      width: "100%"
    },
    chipClose: {
      height: 32,
      padding: 0,
      width: 32
    },
    chipContainer: {
      display: "flex",
      flexDirection: "column",
      marginTop: theme.spacing.unit
    },
    chipInner: {
      "& svg": {
        color: theme.palette.primary.contrastText
      },
      alignItems: "center",
      background: fade(theme.palette.primary.main, 0.6),
      borderRadius: 24,
      color: theme.palette.primary.contrastText,
      display: "flex",
      justifyContent: "space-between",
      margin: `${theme.spacing.unit}px 0`,
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: theme.spacing.unit
    },
    chipLabel: {
      color: theme.palette.primary.contrastText
    },
    container: {
      flexGrow: 1,
      position: "relative"
    },
    hr: {
      margin: `${theme.spacing.unit}px 0`
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
  allowCustomValues?: boolean;
  displayValues: MultiAutocompleteChoiceType[];
  name: string;
  choices: MultiAutocompleteChoiceType[];
  value: string[];
  loading?: boolean;
  placeholder?: string;
  helperText?: string;
  label?: string;
  fetchChoices?: (value: string) => void;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const DebounceAutocomplete: React.ComponentType<
  DebounceProps<string>
> = Debounce;

export const MultiAutocompleteSelectFieldComponent = withStyles(styles, {
  name: "MultiAutocompleteSelectField"
})(
  ({
    allowCustomValues,
    choices,
    classes,
    displayValues,
    helperText,
    label,
    loading,
    name,
    placeholder,
    value,
    fetchChoices,
    onChange
  }: MultiAutocompleteSelectFieldProps & WithStyles<typeof styles>) => {
    const handleSelect = (
      item: string,
      downshiftOpts?: ControllerStateAndHelpers
    ) => {
      if (downshiftOpts) {
        downshiftOpts.reset({ inputValue: "" });
      }
      onChange({
        target: { name, value: item }
      } as any);
    };
    const suggestions = choices.filter(choice => !value.includes(choice.value));

    return (
      <>
        <Downshift
          onInputValueChange={fetchChoices}
          onSelect={handleSelect}
          itemToString={() => ""}
        >
          {({
            getInputProps,
            getItemProps,
            isOpen,
            toggleMenu,
            highlightedIndex,
            inputValue
          }) => (
            <div className={classes.container}>
              <TextField
                InputProps={{
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
                  id: undefined,
                  onClick: toggleMenu
                }}
                helperText={helperText}
                label={label}
                fullWidth={true}
              />
              {isOpen && (!!inputValue || !!choices.length) && (
                <Paper className={classes.paper} square>
                  {choices.length > 0 ||
                  displayValues.length > 0 ||
                  allowCustomValues ? (
                    <>
                      {displayValues.map(value => (
                        <MenuItem
                          key={value.value}
                          selected={true}
                          component="div"
                          {...getItemProps({
                            item: value.value
                          })}
                        >
                          <Checkbox checked={true} disableRipple />
                          {value.label}
                        </MenuItem>
                      ))}
                      {displayValues.length > 0 && suggestions.length > 0 && (
                        <Hr className={classes.hr} />
                      )}
                      {suggestions.map((suggestion, index) => (
                        <MenuItem
                          key={suggestion.value}
                          selected={highlightedIndex === index + value.length}
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
                      ))}
                      {allowCustomValues &&
                        inputValue &&
                        !choices.find(
                          choice =>
                            choice.label.toLowerCase() ===
                            inputValue.toLowerCase()
                        ) && (
                          <MenuItem
                            key={"customValue"}
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
                    !loading && (
                      <MenuItem disabled={true} component="div">
                        {i18n.t("No results found")}
                      </MenuItem>
                    )
                  )}
                </Paper>
              )}
            </div>
          )}
        </Downshift>
        <div className={classes.chipContainer}>
          {displayValues.map(value => (
            <div className={classes.chip} key={value.value}>
              <div className={classes.chipInner}>
                <Typography className={classes.chipLabel} variant="caption">
                  {value.label}
                </Typography>
                <IconButton
                  className={classes.chipClose}
                  onClick={() => handleSelect(value.value)}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </div>
            </div>
          ))}
        </div>
      </>
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
