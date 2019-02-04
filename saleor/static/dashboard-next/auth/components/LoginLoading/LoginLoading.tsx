import CircularProgress from "@material-ui/core/CircularProgress";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

const styles = createStyles({
  root: {
    alignItems: "center",
    display: "flex",
    height: "100vh",
    justifyContent: "center"
  }
});
const LoginLoading = withStyles(styles, { name: "LoginLoading" })(
  ({ classes }: WithStyles<typeof styles>) => (
    <div className={classes.root}>
      <CircularProgress size={128} />
    </div>
  )
);
LoginLoading.displayName = "LoginLoading";
export default LoginLoading;
