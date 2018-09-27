import Button from "@material-ui/core/Button";
import { withStyles, WithStyles } from "@material-ui/core/styles";
import TextField, { TextFieldProps } from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import CloseIcon from "@material-ui/icons/Close";
import * as React from "react";
import i18n from "../../i18n";

interface ListFieldProps
  extends Exclude<Exclude<TextFieldProps, "value">, "classes"> {
  values: string[];
}

interface ListFieldState {
  value: string;
}

const decorate = withStyles(theme => ({
  chip: {
    background: "rgba(90, 179, 120, .1)",
    borderRadius: 8,
    display: "inline-block" as "inline-block",
    marginRight: theme.spacing.unit * 2,
    padding: "4px 8px"
  },
  chipContainer: {
    marginTop: theme.spacing.unit * 2,
    width: 552
  },
  closeIcon: {
    cursor: "pointer" as "pointer",
    fontSize: 16,
    verticalAlign: "middle" as "middle"
  }
}));
const ListField = decorate<
  ListFieldProps & WithStyles<"chip" | "chipContainer" | "closeIcon">
>(
  class ListFieldComponent extends React.Component<
    ListFieldProps & WithStyles<"chip" | "chipContainer" | "closeIcon">,
    ListFieldState
  > {
    state: ListFieldState = {
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
            value: [...this.props.values, this.state.value]
          }
        } as any);
        this.setState({ value: "" });
      }
    };

    handleValueRemove = (index: number) =>
      this.props.onChange({
        target: {
          name: this.props.name,
          value: this.props.values
            .slice(0, index)
            .concat(this.props.values.slice(index + 1, -1))
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
                  variant="flat"
                  color="secondary"
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
              <div className={classes.chip} key={valueIndex}>
                <Typography variant="caption">
                  {value}{" "}
                  <CloseIcon
                    className={classes.closeIcon}
                    onClick={() => this.handleValueRemove(valueIndex)}
                  />
                </Typography>
              </div>
            ))}
          </div>
        </div>
      );
    }
  }
);
ListField.displayName = "ListField";
export default ListField;
