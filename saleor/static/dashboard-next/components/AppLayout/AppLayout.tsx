import AppBar from "@material-ui/core/AppBar";
import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Grow from "@material-ui/core/Grow";
import Hidden from "@material-ui/core/Hidden";
import IconButton from "@material-ui/core/IconButton";
import LinearProgress from "@material-ui/core/LinearProgress";
import MenuItem from "@material-ui/core/MenuItem";
import Menu from "@material-ui/core/MenuList";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import MenuIcon from "@material-ui/icons/Menu";
import Person from "@material-ui/icons/Person";
import SettingsIcon from "@material-ui/icons/Settings";
import * as classNames from "classnames";
import * as React from "react";
import SVG from "react-inlinesvg";

import { appMountPoint } from "../../";
import * as saleorLogo from "../../../images/logo.svg";
import { UserContext } from "../../auth";
import { drawerWidth } from "../../components/AppLayout/consts";
import MenuList from "../../components/AppLayout/MenuList";
import menuStructure from "../../components/AppLayout/menuStructure";
import ResponsiveDrawer from "../../components/AppLayout/ResponsiveDrawer";
import AppProgress from "../../components/AppProgress";
import MenuToggle from "../../components/MenuToggle";
import Navigator from "../../components/Navigator";
import Anchor from "../../components/TextFieldWithChoice/Anchor";
import Toggle from "../../components/Toggle";
import { configurationMenu, configurationMenuUrl } from "../../configuration";
import i18n from "../../i18n";
import ArrowDropdown from "../../icons/ArrowDropdown";
import { removeDoubleSlashes } from "../../misc";

const styles = (theme: Theme) =>
  createStyles({
    appBar: {
      boxShadow: "none",
      display: "grid",
      gridTemplateColumns: `${drawerWidth}px 1fr`,
      zIndex: theme.zIndex.drawer + 1
    },
    appFrame: {
      display: "flex",
      width: "100%",
      zIndex: 1
    },
    appLoader: {
      gridColumn: "span 2",
      height: 2
    },
    arrow: {
      marginLeft: theme.spacing.unit * 2,
      position: "relative",
      top: 6,
      transition: theme.transitions.duration.standard + "ms"
    },
    container: {
      textAlign: "right",
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
      display: "flex",
      flexDirection: "column",
      height: "100%",
      marginLeft: theme.spacing.unit * 4,
      marginTop: theme.spacing.unit * 2,
      paddingBottom: theme.spacing.unit * 3
    },
    menuListItem: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      alignItems: "center",
      color: "#616161",
      display: "flex",
      height: 40,
      paddingLeft: 0,
      textDecoration: "none",
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListItemText: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      cursor: "pointer",
      fontSize: "1rem",
      marginLeft: theme.spacing.unit * 2,
      transition: theme.transitions.duration.standard + "ms"
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
      textAlign: "right"
    }
  });

interface AppLayoutProps {
  children: React.ReactNode;
}
const AppLayout = withStyles(styles, {
  name: "AppLayout"
})(({ classes, children }: AppLayoutProps & WithStyles<typeof styles>) => (
  <AppProgress>
    {({ value: isProgressVisible }) => (
      <UserContext.Consumer>
        {({ logout, user }) => (
          <Navigator>
            {navigate => (
              <Toggle>
                {(
                  isDrawerOpened,
                  { toggle: toggleDrawer, disable: closeDrawer }
                ) => {
                  const handleMenuItemClick = (
                    url: string,
                    event: React.MouseEvent<any>
                  ) => {
                    event.preventDefault();
                    closeDrawer();
                    navigate(url);
                  };
                  return (
                    <div className={classes.appFrame}>
                      <AppBar className={classes.appBar}>
                        <Toolbar disableGutters className={classes.toolBarMenu}>
                          <IconButton
                            color="inherit"
                            aria-label="open drawer"
                            onClick={toggleDrawer}
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
                                <Anchor>
                                  {anchor => (
                                    <>
                                      <div
                                        className={classes.email}
                                        ref={anchor}
                                        onClick={
                                          !menuOpen ? openMenu : undefined
                                        }
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
                                          <IconButton
                                            className={classes.userIcon}
                                          >
                                            <Person />
                                          </IconButton>
                                        </Hidden>
                                      </div>
                                      <Popper
                                        open={menuOpen}
                                        anchorEl={anchor.current}
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
                                                    className={
                                                      classes.userMenuItem
                                                    }
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
                                  )}
                                </Anchor>
                              );
                            }}
                          </MenuToggle>
                        </Toolbar>
                        {isProgressVisible && (
                          <LinearProgress
                            className={classes.appLoader}
                            color="secondary"
                          />
                        )}
                      </AppBar>
                      <ResponsiveDrawer
                        onClose={closeDrawer}
                        open={isDrawerOpened}
                      >
                        <div className={classes.menuList}>
                          <MenuList
                            menuItems={menuStructure}
                            user={user}
                            onMenuItemClick={handleMenuItemClick}
                          />
                          <div className={classes.spacer} />
                          {configurationMenu.filter(menuItem =>
                            user.permissions
                              .map(perm => perm.code)
                              .includes(menuItem.permission)
                          ).length > 0 && (
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
                          )}
                        </div>
                      </ResponsiveDrawer>
                      <main className={classes.content}>{children}</main>
                    </div>
                  );
                }}
              </Toggle>
            )}
          </Navigator>
        )}
      </UserContext.Consumer>
    )}
  </AppProgress>
));

export default AppLayout;
