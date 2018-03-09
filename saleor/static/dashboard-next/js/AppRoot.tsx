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
  appFrame: {
    zIndex: 1,
    display: "flex",
    width: "100%"
  },
  appBar: {
    position: "absolute" as "absolute",
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen
    })
  },
  appBarShift: {
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen
    })
  },
  menuButton: {
    marginLeft: 12,
    marginRight: 20
  },
  hide: {
    display: "none"
  },
  drawerPaper: {
    position: "relative" as "relative",
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
    marginLeft: -drawerWidth,
    padding: theme.spacing.unit * 3,
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen
    })
  },
  contentShift: {
    marginLeft: 0,
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen
    })
  }
}));

const LinkItem = ListItem as React.ComponentType<ListItemProps & LinkProps>;

interface AppRootProps {}

interface AppRootState {
  open: boolean;
}

export const AppRoot = decorate<AppRootProps>(
  class AppRoot extends React.Component<
    AppRootProps &
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
          <AppBar
            className={classNames(classes.appBar, {
              [classes.appBarShift]: open
            })}
          >
            <Toolbar disableGutters={!open}>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                onClick={() => this.setState({ open: true })}
                className={classNames(classes.menuButton, open && classes.hide)}
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
            anchor="left"
            open={open}
            classes={{
              paper: classes.drawerPaper
            }}
          >
            <div className={classes.drawerHeader}>
              <IconButton onClick={() => this.setState({ open: false })}>
                <ChevronLeftIcon />
              </IconButton>
            </div>
            <Divider />
            <List component="nav">
              <LinkItem component={Link} to="/">
                <ListItemText primary={i18n.t("Home")} />
              </LinkItem>
              <LinkItem component={Link} to="/categories/">
                <ListItemText primary={i18n.t("Categories")} />
              </LinkItem>
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
