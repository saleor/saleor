import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface CardSpacerProps {
  children?: React.ReactNode;
}

const decorate = withStyles(theme => ({
  spacer: {
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    },
    marginTop: theme.spacing.unit * 3
  }
}));
export const CardSpacer = decorate<CardSpacerProps>(({ classes, children }) => (
  <div className={classes.spacer}>{children}</div>
));

CardSpacer.displayName = "CardSpacer";
export default CardSpacer;
