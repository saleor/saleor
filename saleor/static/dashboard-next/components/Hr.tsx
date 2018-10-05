import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

const decorate = withStyles({
  root: {
    backgroundColor: "#eeeeee",
    border: "none",
    display: "block" as "block",
    height: 1,
    margin: 0,
    width: "100%"
  }
});
export const Hr = decorate(({ classes }) => <hr className={classes.root} />);
Hr.displayName = "Hr";
export default Hr;
