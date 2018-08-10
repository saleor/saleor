import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface AppLayoutProps {}

const decorate = withStyles(theme => ({
  root: {
    height: theme.spacing.unit * 7
  },
  navbarAside: {
    backgroundColor: theme.palette.primary.dark
  },
  navbarMain: {
    backgroundColor: theme.palette.primary.main
  }
}));
const AppLayout = decorate<AppLayoutProps>(({ classes, children }) => (
  <>
    <div className={classes.root}>
      <div className={classes.navbarAside}>asd</div>
      <div className={classes.navbarMain}>asd</div>
    </div>
    <aside>asd</aside>
    <main>{children}</main>
  </>
));
AppLayout.displayName = "AppLayout";
export default AppLayout;
