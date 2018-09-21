import CircularProgress from "@material-ui/core/CircularProgress";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

const decorate = withStyles({
  root: {
    alignItems: "center" as "center",
    display: "flex" as "flex",
    height: "100vh",
    justifyContent: "center" as "center"
  }
});
const LoginLoading = decorate<{}>(({ classes }) => (
  <div className={classes.root}>
    <CircularProgress size={128} />
  </div>
));
LoginLoading.displayName = "LoginLoading";
export default LoginLoading;
