import AppBar from "@material-ui/core/AppBar";
import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Drawer from "@material-ui/core/Drawer";
import Grow from "@material-ui/core/Grow";
import Hidden from "@material-ui/core/Hidden";
import IconButton from "@material-ui/core/IconButton";
import MenuItem from "@material-ui/core/MenuItem";
import Menu from "@material-ui/core/MenuList";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import { withStyles, WithStyles } from "@material-ui/core/styles";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import MenuIcon from "@material-ui/icons/Menu";
import * as React from "react";
import SVG from "react-inlinesvg";

import * as saleorLogo from "../images/logo.svg";
import { UserContext } from "./auth";
import Container from "./components/Container";
import MenuToggle from "./components/MenuToggle";
import Navigator from "./components/Navigator";
import Toggle from "./components/Toggle";
import i18n from "./i18n";
import ArrowDropdown from "./icons/ArrowDropdown";
import Home from "./icons/Home";
import Shop from "./icons/Shop";

const drawerWidth = 256;

const menuStructure = [
  {
    ariaLabel: "home",
    icon: <Home />,
    label: i18n.t("Home", { context: "Menu label" }),
    url: "/"
  },
  {
    ariaLabel: "catalogue",
    children: [
      {
        ariaLabel: "products",
        icon: <Shop />,
        label: i18n.t("Products", { context: "Menu label" }),
        url: "/products/"
      },
      {
        ariaLabel: "categories",
        icon: <Shop />,
        label: i18n.t("Categories", { context: "Menu label" }),
        url: "/categories/"
      }
    ],
    icon: <Shop />,
    label: i18n.t("Catalogue", { context: "Menu label" })
  }
];

const decorate = withStyles(
  theme => ({
    appBar: {
      boxShadow: "none",
      display: "grid" as "grid",
      gridTemplateColumns: `${drawerWidth}px 1fr`,
      zIndex: theme.zIndex.drawer + 1
    },
    appFrame: {
      display: "flex",
      width: "100%",
      zIndex: 1
    },
    arrow: {
      marginLeft: theme.spacing.unit * 3,
      position: "relative" as "relative",
      top: 6,
      transition: theme.transitions.duration.standard + "ms"
    },
    container: {
      textAlign: "right" as "right",
      width: "100%"
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
      marginTop: 64 + theme.spacing.unit * 2,
      position: "relative" as "relative",
      width: drawerWidth
    },
    email: {
      cursor: "pointer" as "pointer",
      display: "inline" as "inline"
    },
    emailLabel: {
      color: theme.palette.primary.contrastText,
      display: "inline",
      fontWeight: 600 as 600
    },
    logo: {
      "& svg": {
        height: "100%"
      },
      height: 32
    },
    menuButton: {
      marginRight: theme.spacing.unit
    },
    menuList: {
      marginLeft: theme.spacing.unit * 4
    },
    menuListItem: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      alignItems: "center" as "center",
      color: "#616161",
      display: "flex" as "flex",
      height: 40,
      paddingLeft: 0,
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListItemText: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      cursor: "pointer" as "pointer",
      fontSize: "1rem",
      marginLeft: theme.spacing.unit * 2,
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListNested: {
      marginLeft: theme.spacing.unit * 3
    },
    root: {
      flexGrow: 1
    },
    rotate: {
      transform: "rotate(180deg)"
    },
    spacer: {
      flex: 1
    },
    toolBarContent: {
      backgroundColor: "#56D799"
    },
    toolBarMenu: {
      minHeight: 56,
      paddingLeft: theme.spacing.unit
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

interface IMenuItem {
  ariaLabel: string;
  children?: IMenuItem[];
  icon: React.ReactNode;
  label: string;
  url?: string;
}
interface MenuListProps {
  menuItems: IMenuItem[];
  onMenuItemClick: (url: string) => void;
}
const MenuList = decorate<MenuListProps>(
  ({ classes, menuItems, onMenuItemClick }) => (
    <div>
      {menuItems.map(menuItem => {
        if (!menuItem.url) {
          return (
            <Toggle key={menuItem.label}>
              {(openedMenu, { toggle: toggleMenu }) => (
                <>
                  <div onClick={toggleMenu} className={classes.menuListItem}>
                    {menuItem.icon}
                    <Typography
                      aria-label={menuItem.ariaLabel}
                      className={classes.menuListItemText}
                    >
                      {menuItem.label}
                    </Typography>
                  </div>
                  {openedMenu && (
                    <div className={classes.menuListNested}>
                      <MenuList
                        menuItems={menuItem.children}
                        onMenuItemClick={onMenuItemClick}
                      />
                    </div>
                  )}
                </>
              )}
            </Toggle>
          );
        }
        return (
          <div
            className={classes.menuListItem}
            onClick={() => onMenuItemClick(menuItem.url)}
            key={menuItem.label}
          >
            {menuItem.icon}
            <Typography
              aria-label={menuItem.ariaLabel}
              className={classes.menuListItemText}
            >
              {menuItem.label}
            </Typography>
          </div>
        );
      })}
    </div>
  )
);

interface AppRootState {
  open: boolean;
}

export const AppRoot = decorate(
  class InnerAppRoot extends React.Component<
    WithStyles<
      | "appBar"
      | "appFrame"
      | "arrow"
      | "content"
      | "contentShift"
      | "container"
      | "drawerDesktop"
      | "email"
      | "emailLabel"
      | "hide"
      | "logo"
      | "menuButton"
      | "menuList"
      | "menuListItem"
      | "menuListItemText"
      | "menuListNested"
      | "root"
      | "rotate"
      | "spacer"
      | "toolBarContent"
      | "toolBarMenu"
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
        <UserContext.Consumer>
          {({ logout, user }) => (
            <Navigator>
              {navigate => (
                <div className={classes.appFrame}>
                  <AppBar className={classes.appBar}>
                    <Toolbar disableGutters className={classes.toolBarMenu}>
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
                      <SVG className={classes.logo} src={saleorLogo} />
                    </Toolbar>
                    <Toolbar disableGutters className={classes.toolBarContent}>
                      <Container className={classes.container} width="md">
                        <div className={classes.spacer} />
                        <MenuToggle ariaOwns="user-menu">
                          {({
                            anchor,
                            actions: { open: openMenu, close: closeMenu }
                          }) => {
                            const handleLogout = () => {
                              close();
                              logout();
                            };
                            return (
                              <>
                                <div
                                  className={classes.email}
                                  onClick={!!anchor ? closeMenu : openMenu}
                                >
                                  <Typography
                                    className={classes.emailLabel}
                                    component="span"
                                    variant="subheading"
                                  >
                                    {user.email}
                                  </Typography>
                                  <ArrowDropdown
                                    className={[
                                      classes.arrow,
                                      !!anchor ? classes.rotate : undefined
                                    ].join(" ")}
                                  />
                                </div>
                                <Popper
                                  open={!!anchor}
                                  anchorEl={anchor}
                                  transition
                                  disablePortal
                                >
                                  {({ TransitionProps, placement }) => (
                                    <Grow
                                      {...TransitionProps}
                                      style={{
                                        transformOrigin:
                                          placement === "bottom"
                                            ? "right top"
                                            : "right bottom"
                                      }}
                                    >
                                      <Paper>
                                        <ClickAwayListener
                                          onClickAway={closeMenu}
                                        >
                                          <Menu>
                                            <MenuItem onClick={handleLogout}>
                                              {i18n.t("Logout", {
                                                context: "button"
                                              })}
                                            </MenuItem>
                                          </Menu>
                                        </ClickAwayListener>
                                      </Paper>
                                    </Grow>
                                  )}
                                </Popper>
                              </>
                            );
                          }}
                        </MenuToggle>
                      </Container>
                    </Toolbar>
                  </AppBar>
                  <ResponsiveDrawer onClose={this.closeDrawer} open={open}>
                    <div className={classes.menuList}>
                      <MenuList
                        menuItems={menuStructure}
                        onMenuItemClick={navigate}
                      />
                    </div>
                  </ResponsiveDrawer>
                  <main className={classes.content}>{children}</main>
                </div>
              )}
            </Navigator>
          )}
        </UserContext.Consumer>
      );
    }
  }
);

export default AppRoot;
