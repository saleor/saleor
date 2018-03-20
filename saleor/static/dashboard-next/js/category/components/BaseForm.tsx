import Button from "material-ui/Button";
import Card, { CardActions, CardContent } from "material-ui/Card";
import { withStyles, WithStyles } from "material-ui/styles";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import * as React from "react";

import TextField from "material-ui/TextField";
import i18n from "../../i18n";

const { Component } = React;

const decorate = withStyles(theme => ({
  cardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  },
  textField: {
    marginBottom: "2rem"
  }
}));

interface BaseCategoryFormProps {
  confirmButtonLabel: string;
  description: string;
  errors: Array<{
    field: string;
    message: string;
  }>;
  name: string;
  handleConfirm(data);
}

interface BaseCategoryFormState {
  formData: {
    description: string;
    name: string;
  };
}

export const BaseCategoryForm = decorate(
  class InnerBaseCategoryForm extends Component<
    BaseCategoryFormProps & WithStyles<"cardActions" | "textField">,
    BaseCategoryFormState
  > {
    state = {
      formData: {
        description: this.props.description,
        name: this.props.name
      }
    };

    handleInputChange = event => {
      const { target } = event;
      this.setState(prevState => ({
        formData: { ...prevState.formData, [target.name]: target.value }
      }));
    };

    render() {
      const {
        classes,
        confirmButtonLabel,
        description,
        handleConfirm,
        name,
        errors
      } = this.props;
      const errorList: { [key: string]: string } = errors.reduce(
        (acc, curr) => {
          acc[curr.field] = curr.message;
          return acc;
        },
        {}
      );
      return (
        <>
          <CardContent>
            <TextField
              autoFocus
              fullWidth
              className={classes.textField}
              defaultValue={name}
              error={!!errorList.name}
              helperText={errorList.name}
              label={i18n.t("Name", { context: "category" })}
              name="name"
              onChange={this.handleInputChange}
            />
            <TextField
              fullWidth
              multiline
              defaultValue={description}
              error={!!errorList.description}
              helperText={
                errorList.description ||
                i18n.t("Optional", { context: "field" })
              }
              label={i18n.t("Description")}
              name="description"
              onChange={this.handleInputChange}
            />
          </CardContent>
          <Toolbar className={classes.cardActions}>
            <Button
              variant="raised"
              color="primary"
              onClick={() => handleConfirm(this.state.formData)}
            >
              {confirmButtonLabel}
            </Button>
          </Toolbar>
        </>
      );
    }
  }
);

export default BaseCategoryForm;
