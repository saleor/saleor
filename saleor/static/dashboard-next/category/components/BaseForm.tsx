import Button from "material-ui/Button";
import { CardContent } from "material-ui/Card";
import { withStyles, WithStyles } from "material-ui/styles";
import Toolbar from "material-ui/Toolbar";
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
  description: string;
  errors: Array<{
    field: string;
    message: string;
  }>;
  name: string;
  onChange?(event: React.ChangeEvent<any>);
}

export const BaseCategoryForm = decorate<BaseCategoryFormProps>(
  ({ classes, description, errors, name, onChange }) => {
    const errorList: { [key: string]: string } = errors.reduce((acc, curr) => {
      acc[curr.field] = curr.message;
      return acc;
    }, {});
    return (
      <CardContent>
        <TextField
          autoFocus
          fullWidth
          className={classes.textField}
          value={name}
          error={!!errorList.name}
          helperText={errorList.name}
          label={i18n.t("Name", { context: "category" })}
          name="name"
          onChange={onChange}
        />
        <TextField
          fullWidth
          multiline
          value={description}
          error={!!errorList.description}
          helperText={
            errorList.description || i18n.t("Optional", { context: "field" })
          }
          label={i18n.t("Description")}
          name="description"
          onChange={onChange}
        />
      </CardContent>
    );
  }
);

export default BaseCategoryForm;
