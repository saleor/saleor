import Button from "@material-ui/core/Button";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Toolbar from "@material-ui/core/Toolbar";
import * as React from "react";

import i18n from "../../i18n";

const styles = createStyles({
  cardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  }
});

interface FormActionsProps extends WithStyles<typeof styles> {
  submitLabel: string;
  onCancel?();
  onSubmit?(event: React.FormEvent<any>);
}

const FormActions = withStyles(styles, { name: "FormActions" })(
  ({ classes, onCancel, onSubmit, submitLabel }: FormActionsProps) => (
    <Toolbar className={classes.cardActions}>
      <Button
        variant="contained"
        color="primary"
        onClick={onSubmit}
        type="submit"
      >
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
FormActions.displayName = "FormActions";
export default FormActions;
