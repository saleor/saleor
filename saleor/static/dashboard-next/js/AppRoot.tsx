import AppBar from "material-ui/AppBar";
import Divider from "material-ui/Divider";
import Drawer from "material-ui/Drawer";
import Hidden from "material-ui/Hidden";
import IconButton from "material-ui/IconButton";
import List, { ListItem, ListItemText } from "material-ui/List";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import { withStyles, WithStyles } from "material-ui/styles";
import MenuIcon from "material-ui-icons/Menu";
import ChevronLeftIcon from "material-ui-icons/ChevronLeft";
import { Link, LinkProps } from "react-router-dom";
import { ListItemProps } from "material-ui/List";
import * as React from "react";

import i18n from "./i18n";

const drawerWidth = 240;

const decorate = withStyles(theme => ({
  root: {
    flexGrow: 1
  },
  appBar: {
    zIndex: theme.zIndex.drawer + 1
  },
  toolBar: {
    minHeight: 56,
    paddingLeft: theme.spacing.unit,
    [theme.breakpoints.up("md")]: {
      paddingLeft: theme.spacing.unit * 3
    }
  },
  appFrame: {
    zIndex: 1,
    display: "flex",
    width: "100%"
  },
  menuButton: {
    marginRight: theme.spacing.unit * 2
  },
  hide: {
    display: "none"
  },
  drawerDesktop: {
    backgroundColor: "transparent",
    borderRight: "0 none",
    marginTop: 56,
    position: "relative" as "relative",
    width: drawerWidth
  },
  content: {
    flexGrow: 1,
    backgroundColor: theme.palette.background.default,
    marginLeft: 0,
    marginTop: 56,
    padding: theme.spacing.unit,
    [theme.breakpoints.up("sm")]: {
      padding: theme.spacing.unit * 2
    }
  }
}));

interface ResponsiveDrawerProps {
  onClose?();
  open: boolean;
}

const ResponsiveDrawer = decorate<ResponsiveDrawerProps>(
  ({ children, classes, onClose, open }) => (
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
        <Drawer variant="temporary" onClose={onClose} open={open}>
          {children}
        </Drawer>
      </Hidden>
    </>
  )
);

interface AppRootState {
  open: boolean;
}

export const AppRoot = decorate<{}>(
  class AppRoot extends React.Component<
    WithStyles<
      | "root"
      | "appFrame"
      | "appBar"
      | "menuButton"
      | "hide"
      | "drawerDesktop"
      | "content"
      | "contentShift"
      | "toolBar"
    >,
    AppRootState
  > {
    state = { open: false };

    closeDrawer = () => {
      this.setState({ open: false });
    };

    render() {
      const { children, classes } = this.props;
      const { open } = this.state;

      return (
        <div className={classes.appFrame}>
          <AppBar className={classes.appBar}>
            <Toolbar disableGutters className={classes.toolBar}>
              <Hidden mdUp>
                <IconButton
                  color="inherit"
                  aria-label="open drawer"
                  onClick={() =>
                    this.setState(({ open }) => ({
                      open: !open
                    }))
                  }
                  className={classes.menuButton}
                >
                  <MenuIcon />
                </IconButton>
              </Hidden>
              <Typography
                noWrap
                variant="title"
                color="inherit"
                dangerouslySetInnerHTML={{
                  __html: i18n.t("<strong>Saleor</strong> Dashboard")
                }}
              />
            </Toolbar>
          </AppBar>
          <ResponsiveDrawer onClose={this.closeDrawer} open={open}>
            <List component="nav">
              <ListItem
                button
                component={props => <Link to="/" {...props} />}
                onClick={this.closeDrawer}
              >
                <ListItemText primary={i18n.t("Home")} />
              </ListItem>
              <ListItem
                button
                component={props => <Link to="/categories/" {...props} />}
                onClick={this.closeDrawer}
              >
                <ListItemText primary={i18n.t("Categories")} />
              </ListItem>
            </List>
          </ResponsiveDrawer>
          <main className={classes.content}>{children}</main>
        </div>
      );
    }
  }
);

export default AppRoot;
