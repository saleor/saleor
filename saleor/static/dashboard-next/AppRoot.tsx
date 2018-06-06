import AppBar from "@material-ui/core/AppBar";
import Drawer from "@material-ui/core/Drawer";
import Hidden from "@material-ui/core/Hidden";
import IconButton from "@material-ui/core/IconButton";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import { withStyles, WithStyles } from "@material-ui/core/styles";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import MenuIcon from "@material-ui/icons/Menu";
import * as React from "react";

import Navigator from "./components/Navigator";
import i18n from "./i18n";

const drawerWidth = 240;

const decorate = withStyles(
  theme => ({
    appBar: {
      zIndex: theme.zIndex.drawer + 1
    },
    appFrame: {
      display: "flex",
      width: "100%",
      zIndex: 1
    },
    content: {
      backgroundColor: theme.palette.background.default,
      flexGrow: 1,
      marginLeft: 0,
      marginTop: 56,
      padding: theme.spacing.unit,
      [theme.breakpoints.up("sm")]: {
        padding: theme.spacing.unit * 2
      }
    },
    drawerDesktop: {
      backgroundColor: "transparent",
      borderRight: "0 none",
      marginTop: 56,
      position: "relative" as "relative",
      width: drawerWidth
    },
    hide: {
      display: "none"
    },
    menuButton: {
      marginRight: theme.spacing.unit * 2
    },
    root: {
      flexGrow: 1
    },
    toolBar: {
      minHeight: 56,
      paddingLeft: theme.spacing.unit,
      [theme.breakpoints.up("md")]: {
        paddingLeft: theme.spacing.unit * 3
      }
    }
  }),
  { name: "ResponsiveDrawer" }
);

interface ResponsiveDrawerProps {
  open: boolean;
  onClose?();
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
  class InnerAppRoot extends React.Component<
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
        <Navigator>
          {navigate => (
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
                    onClick={() => {
                      this.closeDrawer();
                      navigate("/");
                    }}
                  >
                    <ListItemText primary={i18n.t("Home")} />
                  </ListItem>
                  <ListItem
                    button
                    onClick={() => {
                      this.closeDrawer();
                      navigate("/categories/");
                    }}
                  >
                    <ListItemText primary={i18n.t("Categories")} />
                  </ListItem>
                  <ListItem
                    button
                    onClick={() => {
                      this.closeDrawer();
                      navigate("/pages/");
                    }}
                  >
                    <ListItemText primary={i18n.t("Pages")} />
                  </ListItem>
                  <ListItem
                    button
                    onClick={() => {
                      this.closeDrawer();
                      navigate("/products/");
                    }}
                  >
                    <ListItemText primary={i18n.t("Products")} />
                  </ListItem>
                </List>
              </ResponsiveDrawer>
              <main className={classes.content}>{children}</main>
            </div>
          )}
        </Navigator>
      );
    }
  }
);

export default AppRoot;
