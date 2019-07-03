import { Omit } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField, { StandardTextFieldProps } from "@material-ui/core/TextField";
import React from "react";
import i18n from "../../i18n";
import Chip from "../Chip";

interface ListFieldState {
  newValueCounter: number;
  value: string;
}

const styles = (theme: Theme) =>
  createStyles({
    chip: {
      marginBottom: theme.spacing.unit
    },
    chipContainer: {
      marginTop: theme.spacing.unit * 2,
      width: 552
    }
  });

interface ListFieldProps
  extends Omit<StandardTextFieldProps, "classes">,
    WithStyles<typeof styles> {
  values: Array<{
    label: string;
    value: string;
  }>;
}

const ListField = withStyles(styles)(
  class ListFieldComponent extends React.Component<
    ListFieldProps,
    ListFieldState
  > {
    state: ListFieldState = {
      newValueCounter: 0,
      value: ""
    };
    handleFieldChange = (event: React.ChangeEvent<any>) =>
      this.setState({
        value: event.target.value
      });

    handleFieldSubmit = (event: React.KeyboardEvent<any>) => {
      // Check if pressed 'enter' key
      if (event.keyCode === 13) {
        if (this.state.value !== "") {
          event.preventDefault();
          event.stopPropagation();
          this.handleValueAdd();
        }
      }
    };

    handleValueAdd = () => {
      if (this.state.value !== "") {
        this.props.onChange({
          target: {
            name: this.props.name,
            value: [
              ...this.props.values,
              {
                label: this.state.value,
                value: "generated-" + this.state.newValueCounter
              }
            ]
          }
        } as any);
        this.setState({
          newValueCounter: this.state.newValueCounter + 1,
          value: ""
        });
      }
    };

    handleValueRemove = (index: number) =>
      this.props.onChange({
        target: {
          name: this.props.name,
          value: this.props.values
            .slice(0, index)
            .concat(this.props.values.slice(index + 1))
        }
      } as any);

    render() {
      const { classes, values, onChange, ...props } = this.props;
      return (
        <div>
          <TextField
            {...props}
            InputProps={{
              endAdornment: (
                <Button
                  variant="text"
                  color="primary"
                  onClick={this.handleValueAdd}
                >
                  {i18n.t("Add", { context: "button" })}
                </Button>
              )
            }}
            value={this.state.value}
            onChange={this.handleFieldChange}
            onKeyDown={this.handleFieldSubmit}
          />
          <div className={classes.chipContainer}>
            {values.map((value, valueIndex) => (
              <Chip
                className={classes.chip}
                key={valueIndex}
                label={value.label}
                onClose={() => this.handleValueRemove(valueIndex)}
              />
            ))}
          </div>
        </div>
      );
    }
  }
);
ListField.displayName = "ListField";
export default ListField;
