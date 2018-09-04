import Button from "@material-ui/core/Button";
import { withStyles } from "@material-ui/core/styles";
import Toolbar from "@material-ui/core/Toolbar";
import * as React from "react";

import i18n from "../../i18n";

const decorate = withStyles({
  cardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  }
});

interface FormActionsProps {
  submitLabel: string;
  onCancel?();
  onSubmit?(event: React.FormEvent<any>);
}

const FormActions = decorate<FormActionsProps>(
  ({ classes, onCancel, onSubmit, submitLabel }) => (
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
