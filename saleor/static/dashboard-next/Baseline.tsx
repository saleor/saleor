import CssBaseline from "@material-ui/core/CssBaseline";
import { createStyles, withStyles } from "@material-ui/core/styles";
import React from "react";

const styles = createStyles({
  "@global": {
    "@import": "url('https://rsms.me/inter/inter.css')"
  }
});

const Baseline = withStyles(styles, {
  name: "Baseline"
})(() => <CssBaseline />);
Baseline.displayName = "Baseline";

export default Baseline;
