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
import PersonIcon from "@material-ui/icons/Person";
import SettingsIcon from "@material-ui/icons/Settings";
import * as classNames from "classnames";
import * as React from "react";
import SVG from "react-inlinesvg";

import { appMountPoint } from ".";
import * as saleorLogo from "../images/logo.svg";
import { UserContext } from "./auth";
import { categoryListUrl } from "./categories";
import MenuToggle from "./components/MenuToggle";
import Navigator from "./components/Navigator";
import Toggle from "./components/Toggle";
import { configurationMenuUrl } from "./configuration";
import i18n from "./i18n";
import ArrowDropdown from "./icons/ArrowDropdown";
import Home from "./icons/Home";
import Shop from "./icons/Shop";
import { removeDoubleSlashes } from "./misc";
import { productListUrl } from "./products";

const drawerWidth = 256;
const navigationBarHeight = 64;

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
        url: productListUrl
      },
      {
        ariaLabel: "categories",
        icon: <Shop />,
        label: i18n.t("Categories", { context: "Menu label" }),
        url: categoryListUrl
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
      marginLeft: theme.spacing.unit * 2,
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
        marginLeft: drawerWidth,
        padding: theme.spacing.unit * 2
      }
    },
    drawerDesktop: {
      backgroundColor: "transparent",
      borderRight: "0 none",
      height: `calc(100vh - ${navigationBarHeight + theme.spacing.unit * 2}px)`,
      marginTop: navigationBarHeight + theme.spacing.unit * 2,
      position: "fixed" as "fixed",
      width: drawerWidth
    },
    drawerMobile: {
      width: drawerWidth
    },
    email: {
      cursor: "pointer",
      display: "inline-block",
      height: 48,
      lineHeight: 48 + "px",
      marginRight: theme.spacing.unit * 2
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
      display: "flex" as "flex",
      flexDirection: "column" as "column",
      height: "100%",
      marginLeft: theme.spacing.unit * 4,
      marginTop: theme.spacing.unit * 2,
      paddingBottom: theme.spacing.unit * 3
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
      textDecoration: "none" as "none",
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
    },
    userIcon: {
      marginRight: theme.spacing.unit
    },
    userMenuItem: {
      textAlign: "right" as "right"
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

interface IMenuItem {
  ariaLabel: string;
  children?: IMenuItem[];
  icon: React.ReactNode;
  label: string;
  url?: string;
}
interface MenuListProps {
  menuItems: IMenuItem[];
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
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
          <a
            className={classes.menuListItem}
            href={removeDoubleSlashes(appMountPoint + menuItem.url)}
            onClick={event => onMenuItemClick(menuItem.url, event)}
            key={menuItem.label}
          >
            {menuItem.icon}
            <Typography
              aria-label={menuItem.ariaLabel}
              className={classes.menuListItemText}
            >
              {menuItem.label}
            </Typography>
          </a>
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
      | "drawerMobile"
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
      | "userIcon"
      | "userMenuItem"
    >,
    AppRootState
  > {
    state = { open: false };
    anchor = React.createRef<HTMLDivElement>();

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
              {navigate => {
                const handleMenuItemClick = (
                  url: string,
                  event: React.MouseEvent<any>
                ) => {
                  event.preventDefault();
                  this.closeDrawer();
                  navigate(url);
                };
                return (
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
                      <Toolbar
                        disableGutters
                        className={classes.toolBarContent}
                      >
                        <div className={classes.spacer} />
                        <MenuToggle ariaOwns="user-menu">
                          {({
                            open: menuOpen,
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
                                  ref={this.anchor}
                                  onClick={!menuOpen ? openMenu : undefined}
                                >
                                  <Hidden smDown>
                                    <Typography
                                      className={classes.emailLabel}
                                      component="span"
                                      variant="subheading"
                                    >
                                      {user.email}
                                    </Typography>
                                    <ArrowDropdown
                                      className={classNames({
                                        [classes.arrow]: true,
                                        [classes.rotate]: menuOpen
                                      })}
                                    />
                                  </Hidden>
                                  <Hidden mdUp>
                                    <IconButton className={classes.userIcon}>
                                      <PersonIcon />
                                    </IconButton>
                                  </Hidden>
                                </div>
                                <Popper
                                  open={menuOpen}
                                  anchorEl={this.anchor.current}
                                  transition
                                  disablePortal
                                  placement="bottom-end"
                                >
                                  {({ TransitionProps, placement }) => (
                                    <Grow
                                      {...TransitionProps}
                                      style={{
                                        minWidth: "10rem",
                                        transformOrigin:
                                          placement === "bottom"
                                            ? "right top"
                                            : "right bottom"
                                      }}
                                    >
                                      <Paper>
                                        <ClickAwayListener
                                          onClickAway={closeMenu}
                                          mouseEvent="onClick"
                                        >
                                          <Menu>
                                            <MenuItem
                                              className={classes.userMenuItem}
                                              onClick={handleLogout}
                                            >
                                              {i18n.t("Log out", {
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
                      </Toolbar>
                    </AppBar>
                    <ResponsiveDrawer onClose={this.closeDrawer} open={open}>
                      <div className={classes.menuList}>
                        <MenuList
                          menuItems={menuStructure}
                          onMenuItemClick={handleMenuItemClick}
                        />
                        <div className={classes.spacer} />
                        <a
                          className={classes.menuListItem}
                          href={removeDoubleSlashes(
                            appMountPoint + configurationMenuUrl
                          )}
                          onClick={event =>
                            handleMenuItemClick(configurationMenuUrl, event)
                          }
                        >
                          <SettingsIcon />
                          <Typography
                            aria-label="configure"
                            className={classes.menuListItemText}
                          >
                            {i18n.t("Configure")}
                          </Typography>
                        </a>
                      </div>
                    </ResponsiveDrawer>
                    <main className={classes.content}>{children}</main>
                  </div>
                );
              }}
            </Navigator>
          )}
        </UserContext.Consumer>
      );
    }
  }
);

export default AppRoot;
