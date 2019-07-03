import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import React from "react";

const styles = (theme: Theme) =>
  createStyles({
    spacer: {
      marginTop: theme.spacing.unit * 3
    }
  });

interface FormSpacerProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
}

export const FormSpacer = withStyles(styles, { name: "FormSpacer" })(
  ({ classes, children }: FormSpacerProps) => (
    <div className={classes.spacer}>{children}</div>
  )
);

FormSpacer.displayName = "FormSpacer";
export default FormSpacer;
