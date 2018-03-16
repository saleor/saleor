import * as React from "react";
import { withStyles } from "material-ui/styles";

interface FormSpacerProps {
  children: React.ReactNode;
}

const decorate = withStyles(theme => ({
  spacer: {
    marginTop: theme.spacing.unit * 2
  }
}));
export const FormSpacer = decorate<FormSpacerProps>(({ classes, children }) => (
  <div className={classes.spacer}>{children}</div>
));

export default FormSpacer;
