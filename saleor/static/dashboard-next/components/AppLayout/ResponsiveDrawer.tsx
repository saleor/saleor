import Drawer from "@material-ui/core/Drawer";
import Hidden from "@material-ui/core/Hidden";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";
import { drawerWidth } from "./consts";

const styles = (theme: Theme) =>
  createStyles({
    drawerDesktop: {
      backgroundColor: theme.palette.background.paper,
      border: "none",
      height: "100vh",
      padding: `${theme.spacing.unit * 2}px ${theme.spacing.unit * 4}px`,
      position: "fixed" as "fixed",
      width: drawerWidth
    },
    drawerMobile: {
      padding: `${theme.spacing.unit * 2}px ${theme.spacing.unit * 4}px`,
      width: drawerWidth,
    }
  });

interface ResponsiveDrawerProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  open: boolean;
  onClose?();
}

const ResponsiveDrawer = withStyles(styles, { name: "ResponsiveDrawer" })(
  ({ children, classes, onClose, open }: ResponsiveDrawerProps) => (
    <>
      <Hidden smDown>
        <Drawer
          variant="persistent"
          open
          classes={{
            paper: classes.drawerDesktop
          }}
        >
          {children}
        </Drawer>
      </Hidden>
      <Hidden mdUp>
        <Drawer
          variant="temporary"
          onClose={onClose}
          open={open}
          classes={{ paper: classes.drawerMobile }}
        >
          {children}
        </Drawer>
      </Hidden>
    </>
  )
);
export default ResponsiveDrawer;
