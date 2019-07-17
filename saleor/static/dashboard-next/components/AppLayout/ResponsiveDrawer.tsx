import Drawer from "@material-ui/core/Drawer";
import Hidden from "@material-ui/core/Hidden";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import React from "react";
import { drawerWidth, drawerWidthExpanded } from "./consts";

const styles = (theme: Theme) =>
  createStyles({
    drawerDesktop: {
      backgroundColor: theme.palette.background.paper,
      border: "none",
      height: "100vh",
      overflow: "visible",
      padding: 0,
      position: "fixed" as "fixed",
      transition: "width 0.5s ease",
      width: drawerWidthExpanded
    },
    drawerDesktopSmall: {
      overflow: "visible",
      transition: "width 0.5s ease",
      width: drawerWidth
    },
    drawerMobile: {
      width: drawerWidthExpanded
    }
  });

interface ResponsiveDrawerProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  open: boolean;
  small: boolean;
  onClose?();
}

const ResponsiveDrawer = withStyles(styles, { name: "ResponsiveDrawer" })(
  ({ children, classes, onClose, open, small }: ResponsiveDrawerProps) => (
    <>
      <Hidden smDown>
        <Drawer
          variant="persistent"
          open
          classes={{
            paper: small ? classes.drawerDesktop : classes.drawerDesktopSmall
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
