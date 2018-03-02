import * as React from "react";
import { Component } from "react";
import Button from "material-ui/Button";
import Card, { CardContent, CardActions } from "material-ui/Card";
import Typography from "material-ui/Typography";
import { withStyles, WithStyles } from "material-ui/styles";

import { TextField } from "../../components/inputs";
import { pgettext, gettext } from "../../i18n";

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
        title
      } = this.props;

      return (
        <Card>
          <CardContent>
            <Typography variant="display1">{title}</Typography>
          </CardContent>
          <CardContent>
            <TextField
              name="name"
              label={pgettext("Category form name field label", "Name")}
              defaultValue={name}
              className={classes.textField}
              onChange={this.handleInputChange}
            />
            <TextField
              name="description"
              label={`${pgettext(
                "Category form description field label",
                "Description"
              )} (${gettext("Optional")})`}
              defaultValue={description}
              multiline
              onChange={this.handleInputChange}
            />
          </CardContent>
          <CardContent>
            <CardActions className={classes.cardActions}>
              <Button
                variant="raised"
                color="secondary"
                onClick={handleConfirm(this.state.formData)}
              >
                {confirmButtonLabel}
              </Button>
              <Button color="secondary">
                {pgettext("Dashboard cancel action", "Cancel")}
              </Button>
            </CardActions>
          </CardContent>
        </Card>
      );
    }
  }
);
