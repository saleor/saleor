import * as classNames from "classnames";
import AppBar from "material-ui/AppBar";
import Divider from "material-ui/Divider";
import Drawer from "material-ui/Drawer";
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
  drawerPaper: {
    width: drawerWidth
  },
  drawerHeader: {
    display: "flex",
    alignItems: "center" as "center",
    justifyContent: "flex-end" as "flex-end",
    padding: "0 8px",
    ...theme.mixins.toolbar
  },
  content: {
    flexGrow: 1,
    backgroundColor: theme.palette.background.default,
    marginLeft: 0,
    padding: theme.spacing.unit * 2,
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen
    })
  },
  contentShift: {
    marginLeft: drawerWidth,
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen
    })
  }
}));

interface AppRootState {
  open: boolean;
}

export const AppRoot = decorate<{}>(
  class AppRoot extends React.Component<
    WithStyles<
      | "root"
      | "appFrame"
      | "appBar"
      | "appBarShift"
      | "menuButton"
      | "hide"
      | "drawerPaper"
      | "drawerHeader"
      | "content"
      | "contentShift"
    >,
    AppRootState
  > {
    state = { open: true };

    render() {
      const { children, classes } = this.props;
      const { open } = this.state;

      return (
        <div className={classes.appFrame}>
          <AppBar className={classes.appBar}>
            <Toolbar>
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
              <Typography variant="title" color="inherit" noWrap>
                Saleor
              </Typography>
            </Toolbar>
          </AppBar>
          <Drawer
            variant="persistent"
            open={open}
            classes={{
              paper: classes.drawerPaper
            }}
          >
            <div className={classes.drawerHeader} />
            <List component="nav">
              <ListItem button component={props => <Link to="/" {...props} />}>
                <ListItemText primary={i18n.t("Home")} />
              </ListItem>
              <ListItem
                button
                component={props => <Link to="/categories/" {...props} />}
              >
                <ListItemText primary={i18n.t("Categories")} />
              </ListItem>
            </List>
          </Drawer>
          <main
            className={classNames(classes.content, {
              [classes.contentShift]: open
            })}
          >
            <div className={classes.drawerHeader} />
            {children}
          </main>
        </div>
      );
    }
  }
);

export default AppRoot;
