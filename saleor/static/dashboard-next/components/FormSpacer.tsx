import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface FormSpacerProps {
  children?: React.ReactNode;
}

const decorate = withStyles(theme => ({
  spacer: {
    marginTop: theme.spacing.unit * 3
  }
}));
export const FormSpacer = decorate<FormSpacerProps>(({ classes, children }) => (
  <div className={classes.spacer}>{children}</div>
));

export default FormSpacer;
