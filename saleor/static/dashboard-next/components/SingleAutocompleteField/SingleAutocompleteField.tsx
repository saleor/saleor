import MenuItem from "@material-ui/core/MenuItem";
import Paper from "@material-ui/core/Paper";
import { withStyles, WithStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Downshift from "downshift";
import { filter } from "fuzzaldrin";
import * as React from "react";

import i18n from "../../i18n";

interface SingleAutocompleteFieldProps {
  choices: Array<{
    label?: React.ReactNode;
    name: string;
    value: string;
  }>;
  custom?: boolean;
  disabled?: boolean;
  helperText?: string;
  label?: string;
  name: string;
  placeholder?: string;
  sort?: boolean;
  value: string;
  onChange: (event: React.ChangeEvent<any>) => void;
  onInputChange?: (value: string) => void;
}

interface SingleAutocompleteFieldState {
  name: string;
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
const SingleAutocompleteField = decorate<SingleAutocompleteFieldProps>(
  class SingleAutocompleteFieldComponent extends React.Component<
    SingleAutocompleteFieldProps &
      WithStyles<"container" | "inputRoot" | "paper">,
    SingleAutocompleteFieldState
  > {
    constructor(props) {
      super(props);
      const filteredChoices = this.props.choices.filter(
        choice => choice.value === this.props.value
      );
      const name =
        filteredChoices.length > 0 ? filteredChoices[0].name : this.props.value;
      this.state = { name };
    }

    render() {
      const {
        choices,
        classes,
        custom,
        disabled,
        helperText,
        label,
        name,
        placeholder,
        sort,
        value,
        onChange,
        onInputChange
      } = this.props;
      const handleChange = item => {
        this.setState({ name: item.name });
        onChange({ target: { name, value: item.value } } as any);
      };

      return (
        <Downshift
          defaultInputValue={this.state.name}
          selectedItem={value}
          itemToString={() => this.state.name}
          onSelect={handleChange}
          onInputValueChange={onInputChange}
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
              choices && selectedItem
                ? choices.filter(c => c.value === selectedItem.value).length ===
                  0
                : false;
            return (
              <div className={classes.container}>
                <TextField
                  InputProps={{
                    classes: {
                      root: classes.inputRoot
                    },
                    ...getInputProps({
                      disabled,
                      placeholder
                    })
                  }}
                  helperText={helperText}
                  label={label}
                  fullWidth={true}
                />
                {isOpen && (
                  <Paper className={classes.paper} square>
                    {(sort
                      ? filter(choices, inputValue, { key: "name" })
                      : choices
                    ).map((suggestion, index) => (
                      <MenuItem
                        key={suggestion.value}
                        selected={
                          selectedItem
                            ? suggestion.value === selectedItem.value ||
                              index === highlightedIndex
                            : false
                        }
                        component="div"
                        {...getItemProps({ item: suggestion })}
                      >
                        {suggestion.label ? suggestion.label : suggestion.name}
                      </MenuItem>
                    ))}
                    {custom && (
                      <MenuItem
                        selected={isCustom}
                        component="div"
                        {...getItemProps({
                          item: { label: inputValue, value: inputValue }
                        })}
                      >
                        {i18n.t("Add custom value")}
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
  }
);
SingleAutocompleteField.displayName = "SingleAutocompleteField";
export default SingleAutocompleteField;
