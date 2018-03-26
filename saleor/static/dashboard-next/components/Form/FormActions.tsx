import Button from "material-ui/Button";
import { withStyles } from "material-ui/styles";
import Toolbar from "material-ui/Toolbar";
import * as React from "react";

import i18n from "../../i18n";

const decorate = withStyles(theme => ({
  cardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  }
}));

interface FormActionsProps {
  submitLabel: string;
  onCancel?();
  onSubmit?(event: React.FormEvent<any>);
}

const FormActions = decorate<FormActionsProps>(
  ({ children, classes, onCancel, onSubmit, submitLabel }) => (
    <Toolbar className={classes.cardActions}>
      <Button variant="raised" color="primary" onClick={onSubmit} type="submit">
        {submitLabel}
      </Button>
      {onCancel && (
        <Button onClick={onCancel}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
      )}
    </Toolbar>
  )
);

export default FormActions;
