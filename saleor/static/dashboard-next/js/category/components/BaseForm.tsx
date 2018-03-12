import Button from "material-ui/Button";
import Card, { CardContent, CardActions } from "material-ui/Card";
import Typography from "material-ui/Typography";
import { withStyles, WithStyles } from "material-ui/styles";
import * as React from "react";
import { Component } from "react";

import { TextField } from "../../components/TextField";
import i18n from "../../i18n";

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
  handleConfirm(data);
  name: string;
  title: string;
  errors: Array<{
    field: string;
    message: string;
  }>;
}

interface BaseCategoryFormState {
  formData: {
    description: string;
    name: string;
  };
}

export const BaseCategoryForm = decorate(
  class BaseCategoryForm extends Component<
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
        title,
        errors
      } = this.props;
      const errorList = errors.reduce((acc, curr) => {
        acc[curr.field] = curr.message;
        return acc;
      }, {});
      console.log(errorList);
      return (
        <Card>
          <CardContent>
            <Typography variant="display1">{title}</Typography>
          </CardContent>
          <CardContent>
            <TextField
              autoFocus
              name="name"
              label={i18n.t("Name", { context: "category" })}
              defaultValue={name}
              className={classes.textField}
              onChange={this.handleInputChange}
              error={Boolean(errorList["name"])}
              helperText={errorList["name"]}
            />
            <TextField
              name="description"
              label={i18n.t("Description (optional)")}
              defaultValue={description}
              multiline
              onChange={this.handleInputChange}
              error={Boolean(errorList["description"])}
              helperText={errorList["description"]}
            />
          </CardContent>
          <CardContent>
            <CardActions className={classes.cardActions}>
              <Button
                variant="raised"
                color="primary"
                onClick={() => handleConfirm(this.state.formData)}
              >
                {confirmButtonLabel}
              </Button>
              <Button color="primary" onClick={() => window.history.back()}>
                {i18n.t("Cancel", { context: "button" })}
              </Button>
            </CardActions>
          </CardContent>
        </Card>
      );
    }
  }
);
