import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      backgroundColor: theme.overrides.MuiCard.root.borderColor,
      border: "none",
      display: "block",
      height: 1,
      margin: 0,
      width: "100%"
    }
  });

export const Hr = withStyles(styles, { name: "Hr" })(
  ({ classes }: WithStyles<typeof styles>) => <hr className={classes.root} />
);
Hr.displayName = "Hr";
export default Hr;
